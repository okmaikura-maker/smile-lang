"""Smile Language Debugger - ステップ実行デバッガー"""

import sys
import os
from pathlib import Path


class SmileDebugger:
    def __init__(self, source, filename):
        self.source = source
        self.filename = filename
        self.lines = source.split("\n")
        self.breakpoints = set()
        self.stepping = False
        self.current_line = 0

    def trace(self, frame, event, arg):
        if event == "line":
            lineno = frame.f_lineno
            # prelude行をスキップ
            if frame.f_code.co_filename != self.filename:
                return self.trace
            self.current_line = lineno
            if self.stepping or lineno in self.breakpoints:
                self.show_context(lineno)
                self.interactive(frame)
        return self.trace

    def show_context(self, lineno):
        print(f"\n--- {self.filename}:{lineno} ---")
        start = max(0, lineno - 3)
        end = min(len(self.lines), lineno + 2)
        for i in range(start, end):
            marker = " >> " if i + 1 == lineno else "    "
            print(f"{marker}{i+1:4d} | {self.lines[i]}")
        print()

    def interactive(self, frame):
        while True:
            try:
                cmd = input("debug> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nデバッグ終了")
                sys.settrace(None)
                return

            if cmd in ("n", "next", "次"):
                self.stepping = True
                return
            elif cmd in ("c", "continue", "続行"):
                self.stepping = False
                return
            elif cmd in ("q", "quit", "終了"):
                print("デバッグ終了")
                sys.settrace(None)
                sys.exit(0)
            elif cmd in ("l", "list", "一覧"):
                self.show_context(self.current_line)
            elif cmd.startswith("b ") or cmd.startswith("break "):
                try:
                    line = int(cmd.split()[-1])
                    self.breakpoints.add(line)
                    print(f"ブレークポイント設定: 行 {line}")
                except ValueError:
                    print("使い方: b <行番号>")
            elif cmd.startswith("p ") or cmd.startswith("print "):
                expr = cmd.split(None, 1)[1]
                try:
                    val = eval(expr, frame.f_globals, frame.f_locals)
                    print(f"  {expr} = {val!r}")
                except Exception as e:
                    print(f"  エラー: {e}")
            elif cmd in ("v", "vars", "変数"):
                for k, v in sorted(frame.f_locals.items()):
                    if not k.startswith("_"):
                        print(f"  {k} = {v!r}")
            elif cmd in ("h", "help", "ヘルプ"):
                print("  n/next/次    : 次の行")
                print("  c/continue/続行 : 続行")
                print("  b <行>/break : ブレークポイント設定")
                print("  p <式>/print : 式を評価")
                print("  v/vars/変数  : ローカル変数一覧")
                print("  l/list/一覧  : コード表示")
                print("  q/quit/終了  : 終了")
            else:
                try:
                    val = eval(cmd, frame.f_globals, frame.f_locals)
                    if val is not None:
                        print(f"  = {val!r}")
                except Exception:
                    try:
                        exec(cmd, frame.f_globals, frame.f_locals)
                    except Exception as e:
                        print(f"  エラー: {e}")


def run_debug(filepath):
    from smile.compiler import compile_smile, SMILE_PRELUDE, _get_prelude_globals
    source = Path(filepath).read_text(encoding="utf-8")
    python_code = compile_smile(source, filepath)
    full_code = SMILE_PRELUDE + python_code

    print(f"デバッグモード: {filepath}")
    print("'h' でヘルプ、'n' で次の行、'c' で続行")
    print("-" * 40)

    debugger = SmileDebugger(source, filepath)
    debugger.stepping = True

    globs = dict(_get_prelude_globals())
    globs["__name__"] = "__main__"
    globs["__file__"] = filepath

    code_obj = compile(full_code, filepath, "exec")
    sys.settrace(debugger.trace)
    try:
        exec(code_obj, globs)
    except SystemExit:
        pass
    except Exception as e:
        print(f"\nエラー: {e}")
    finally:
        sys.settrace(None)
    print("\nデバッグ完了")
