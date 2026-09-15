"""Smile Language v0.2 - コンパイラ & ランタイム"""

import sys
import os
import io
import json
from pathlib import Path
from lark import Lark, Tree, Token

def _get_base_path():
    if getattr(sys, '_MEIPASS', None):
        return Path(sys._MEIPASS) / "smile"
    return Path(__file__).parent

GRAMMAR_PATH = _get_base_path() / "grammar.lark"
VERSION = "0.4.0"

if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


# ============================================================
# パーサ (キャッシュ)
# ============================================================
_PARSER_CACHE = None

def create_parser():
    global _PARSER_CACHE
    if _PARSER_CACHE is not None:
        return _PARSER_CACHE
    grammar = GRAMMAR_PATH.read_text(encoding="utf-8")
    _PARSER_CACHE = Lark(grammar, parser="earley", start="start")
    return _PARSER_CACHE


# ============================================================
# コード生成
# ============================================================
class CodeGen:
    def __init__(self):
        self.indent = 0

    def ind(self):
        return "    " * self.indent

    def gen(self, node):
        if isinstance(node, Token):
            return str(node)
        if not isinstance(node, Tree):
            return str(node) if node is not None else ""
        method = getattr(self, f"gen_{node.data}", None)
        if method:
            return method(node)
        return self.gen_children(node)

    def gen_children(self, node):
        parts = []
        for c in node.children:
            r = self.gen(c)
            if r and r.strip():
                parts.append(r)
        return "\n".join(parts)

    def gen_start(self, node):
        return self.gen_children(node)

    # --- Literals ---
    def gen_number(self, node): return str(node.children[0])
    def gen_hex_number(self, node): return str(node.children[0])
    def gen_bin_number(self, node): return str(node.children[0])
    def gen_oct_number(self, node): return str(node.children[0])
    def gen_float_num(self, node): return str(node.children[0])
    def gen_true_lit(self, node): return "True"
    def gen_false_lit(self, node): return "False"
    def gen_none_lit(self, node): return "None"
    def gen_var(self, node): return str(node.children[0])

    def gen_string(self, node):
        return str(node.children[0])

    def gen_fstring(self, node):
        raw = str(node.children[0])
        return "f" + raw[1:]

    def gen_mstring(self, node):
        return str(node.children[0])

    def gen_list_lit(self, node):
        if node.children and node.children[0] is not None:
            return self.gen(node.children[0])
        return "[]"

    def gen_list_items(self, node):
        return "[" + ", ".join(self.gen(c) for c in node.children) + "]"

    def gen_dict_lit(self, node):
        if node.children and node.children[0] is not None:
            return self.gen(node.children[0])
        return "{}"

    def gen_dict_items(self, node):
        return "{" + ", ".join(self.gen(c) for c in node.children) + "}"

    def gen_dict_pair(self, node):
        return f"{self.gen(node.children[0])}: {self.gen(node.children[1])}"

    # --- Ops ---
    def _binop(self, node, op):
        return f"({self.gen(node.children[0])} {op} {self.gen(node.children[1])})"

    def gen_add(self, n): return self._binop(n, "+")
    def gen_sub(self, n): return self._binop(n, "-")
    def gen_mul(self, n): return self._binop(n, "*")
    def gen_div(self, n): return self._binop(n, "/")
    def gen_floordiv(self, n): return self._binop(n, "//")
    def gen_mod(self, n): return self._binop(n, "%")
    def gen_power_op(self, n): return self._binop(n, "**")
    def gen_eq(self, n): return self._binop(n, "==")
    def gen_ne(self, n): return self._binop(n, "!=")
    def gen_lt(self, n): return self._binop(n, "<")
    def gen_gt(self, n): return self._binop(n, ">")
    def gen_le(self, n): return self._binop(n, "<=")
    def gen_ge(self, n): return self._binop(n, ">=")
    def gen_in_op(self, n): return self._binop(n, "in")
    def gen_or_op(self, n): return self._binop(n, "or")
    def gen_and_op(self, n): return self._binop(n, "and")
    def gen_not_op(self, n): return f"(not {self.gen(n.children[0])})"
    def gen_neg(self, n): return f"(-{self.gen(n.children[0])})"

    def gen_pipe(self, node):
        left = self.gen(node.children[0])
        right = self.gen(node.children[1])
        return f"{right}({left})"

    def gen_ternary(self, node):
        value = self.gen(node.children[0])
        cond = self.gen(node.children[1])
        alt = self.gen(node.children[2])
        return f"({value} if {cond} else {alt})"

    def gen_inline_if(self, node):
        value = self.gen(node.children[0])
        cond = self.gen(node.children[1])
        alt = self.gen(node.children[2])
        return f"({value} if {cond} else {alt})"

    # --- Postfix ---
    def gen_call(self, node):
        func = self.gen(node.children[0])
        if len(node.children) > 1 and node.children[1] is not None:
            args = self.gen(node.children[1])
        else:
            args = ""
        return f"{func}({args})"

    def gen_args(self, node):
        return ", ".join(self.gen(c) for c in node.children)

    def gen_posarg(self, node):
        return self.gen(node.children[0])

    def gen_kwarg(self, node):
        return f"{node.children[0]}={self.gen(node.children[1])}"

    def gen_spread_arg(self, node):
        return f"*{self.gen(node.children[0])}"

    def gen_attr(self, node):
        return f"{self.gen(node.children[0])}.{node.children[1]}"

    def gen_index(self, node):
        return f"{self.gen(node.children[0])}[{self.gen(node.children[1])}]"

    # --- Slice ---
    def gen_slice_simple(self, node):
        start = self.gen(node.children[0])
        end = self.gen(node.children[1]) if len(node.children) > 1 and node.children[1] is not None else ""
        return f"{start}:{end}"

    def gen_slice_full(self, node):
        start = self.gen(node.children[0])
        end = self.gen(node.children[1]) if len(node.children) > 1 and node.children[1] is not None else ""
        step = self.gen(node.children[2]) if len(node.children) > 2 and node.children[2] is not None else ""
        return f"{start}:{end}:{step}"

    def gen_slice_from_start_simple(self, node):
        end = self.gen(node.children[0]) if node.children and node.children[0] is not None else ""
        return f":{end}"

    def gen_slice_from_start(self, node):
        end = self.gen(node.children[0]) if len(node.children) > 0 and node.children[0] is not None else ""
        step = self.gen(node.children[1]) if len(node.children) > 1 and node.children[1] is not None else ""
        return f":{end}:{step}"

    # --- Lambda ---
    def gen_lambda_def(self, node):
        if len(node.children) == 2:
            return f"(lambda {self.gen(node.children[0])}: {self.gen(node.children[1])})"
        return f"(lambda: {self.gen(node.children[0])})"

    # --- Params (new: default, rest) ---
    def gen_func_params(self, node):
        return ", ".join(self.gen(c) for c in node.children)

    def gen_normal_param(self, node):
        return str(node.children[0])

    def gen_default_param(self, node):
        return f"{node.children[0]}={self.gen(node.children[1])}"

    def gen_rest_param(self, node):
        return f"*{node.children[0]}"

    def gen_params(self, node):
        return ", ".join(str(c) for c in node.children)

    # --- List comprehension ---
    def gen_list_comp(self, node):
        expr = self.gen(node.children[0])
        var = str(node.children[1])
        iter_expr = self.gen(node.children[2])
        if len(node.children) > 3:
            cond = self.gen(node.children[3])
            return f"[{expr} for {var} in {iter_expr} if {cond}]"
        return f"[{expr} for {var} in {iter_expr}]"

    # --- Statements ---
    def gen_assign(self, node):
        return f"{self.ind()}{node.children[0]} = {self.gen(node.children[1])}"

    def gen_attr_assign(self, node):
        return f"{self.ind()}{self.gen(node.children[0])}.{node.children[1]} = {self.gen(node.children[2])}"

    def gen_index_assign(self, node):
        return f"{self.ind()}{self.gen(node.children[0])}[{self.gen(node.children[1])}] = {self.gen(node.children[2])}"

    def gen_multi_assign(self, node):
        names = []
        exprs = []
        for c in node.children:
            if isinstance(c, Token):
                names.append(str(c))
            else:
                exprs.append(self.gen(c))
        return f"{self.ind()}{', '.join(names)} = {', '.join(exprs)}"

    def gen_aug_add(self, n): return f"{self.ind()}{n.children[0]} += {self.gen(n.children[1])}"
    def gen_aug_sub(self, n): return f"{self.ind()}{n.children[0]} -= {self.gen(n.children[1])}"
    def gen_aug_mul(self, n): return f"{self.ind()}{n.children[0]} *= {self.gen(n.children[1])}"
    def gen_aug_div(self, n): return f"{self.ind()}{n.children[0]} /= {self.gen(n.children[1])}"

    def gen_expr_stmt(self, node):
        return f"{self.ind()}{self.gen(node.children[0])}"

    def gen_return_stmt(self, node):
        if node.children:
            return f"{self.ind()}return {self.gen(node.children[0])}"
        return f"{self.ind()}return"

    def gen_break_stmt(self, _): return f"{self.ind()}break"
    def gen_continue_stmt(self, _): return f"{self.ind()}continue"

    def gen_throw_stmt(self, node):
        return f"{self.ind()}raise {self.gen(node.children[0])}"

    # --- Try/Catch/Finally ---
    def gen_try_stmt(self, node):
        parts = []
        idx = 0
        body = self.gen(node.children[idx])
        parts.append(f"{self.ind()}try:\n{body}")
        idx += 1
        while idx < len(node.children):
            c = node.children[idx]
            if isinstance(c, Tree) and c.data == "catch_clause":
                parts.append(self.gen(c))
            elif isinstance(c, Tree) and c.data == "finally_clause":
                parts.append(self.gen(c))
            idx += 1
        return "\n".join(parts)

    def gen_catch_clause(self, node):
        if len(node.children) == 2 and isinstance(node.children[0], Token):
            var = str(node.children[0])
            body = self.gen(node.children[1])
            return f"{self.ind()}except Exception as {var}:\n{body}"
        else:
            body = self.gen(node.children[-1])
            return f"{self.ind()}except Exception:\n{body}"

    def gen_finally_clause(self, node):
        body = self.gen(node.children[0])
        return f"{self.ind()}finally:\n{body}"

    # --- Import ---
    def gen_import_simple(self, node):
        return f"{self.ind()}import {'.'.join(str(c) for c in node.children)}"

    def gen_import_as(self, node):
        parts = [str(c) for c in node.children]
        return f"{self.ind()}import {'.'.join(parts[:-1])} as {parts[-1]}"

    def gen_import_from(self, node):
        mod = '.'.join(str(c) for c in node.children[:-1])
        names = self.gen(node.children[-1])
        return f"{self.ind()}from {mod} import {names}"

    def gen_import_from_star(self, node):
        return f"{self.ind()}from {'.'.join(str(c) for c in node.children)} import *"

    def gen_import_names(self, node):
        return ", ".join(str(c) for c in node.children)

    # --- Block ---
    def gen_block(self, node):
        self.indent += 1
        lines = []
        for c in node.children:
            if c is not None:
                r = self.gen(c)
                if r and r.strip():
                    lines.append(r)
        if not lines:
            lines.append(f"{self.ind()}pass")
        self.indent -= 1
        return "\n".join(lines)

    # --- If ---
    def gen_if_stmt(self, node):
        children = [c for c in node.children if c is not None]
        result = []
        cond = self.gen(children[0])
        body = self.gen(children[1])
        result.append(f"{self.ind()}if {cond}:\n{body}")
        idx = 2
        while idx + 1 < len(children):
            c = children[idx]
            if isinstance(c, Tree) and c.data == "block":
                body = self.gen(c)
                result.append(f"{self.ind()}else:\n{body}")
                idx += 1
                break
            else:
                cond = self.gen(c)
                body = self.gen(children[idx + 1])
                result.append(f"{self.ind()}elif {cond}:\n{body}")
                idx += 2
        if idx < len(children):
            c = children[idx]
            if isinstance(c, Tree) and c.data == "block":
                body = self.gen(c)
                result.append(f"{self.ind()}else:\n{body}")
        return "\n".join(result)

    def gen_while_stmt(self, node):
        cond = self.gen(node.children[0])
        body = self.gen(node.children[1])
        return f"{self.ind()}while {cond}:\n{body}"

    def gen_for_stmt(self, node):
        var = str(node.children[0])
        iter_expr = self.gen(node.children[1])
        body = self.gen(node.children[2])
        return f"{self.ind()}for {var} in {iter_expr}:\n{body}"

    def gen_for_pair_stmt(self, node):
        var1 = str(node.children[0])
        var2 = str(node.children[1])
        iter_expr = self.gen(node.children[2])
        body = self.gen(node.children[3])
        return f"{self.ind()}for {var1}, {var2} in {iter_expr}:\n{body}"

    # --- Typed params ---
    def gen_typed_params(self, node):
        return ", ".join(self.gen(c) for c in node.children)

    def gen_typed_param_only(self, node):
        return str(node.children[0])

    def gen_typed_default_param(self, node):
        return f"{node.children[0]}={self.gen(node.children[2])}"

    def gen_return_type(self, node):
        return ""

    # --- Decorator ---
    def gen_decorated_def(self, node):
        parts = []
        for c in node.children:
            if isinstance(c, Tree) and c.data == "decorator":
                parts.append(f"{self.ind()}@{self.gen(c.children[0])}")
            else:
                parts.append(self.gen(c))
        return "\n".join(parts)

    # --- Function ---
    def gen_func_def(self, node):
        name = str(node.children[0])
        children = [c for c in node.children if not (isinstance(c, Tree) and c.data == "return_type")]
        if len(children) == 3:
            params = self.gen(children[1])
            body = self.gen(children[2])
        else:
            params = ""
            body = self.gen(children[1])
        return f"{self.ind()}def {name}({params}):\n{body}"

    def gen_async_func_def(self, node):
        name = str(node.children[0])
        children = [c for c in node.children if not (isinstance(c, Tree) and c.data == "return_type")]
        if len(children) == 3:
            params = self.gen(children[1])
            body = self.gen(children[2])
        else:
            params = ""
            body = self.gen(children[1])
        return f"{self.ind()}async def {name}({params}):\n{body}"

    # --- Await ---
    def gen_await_expr(self, node):
        return f"(await {self.gen(node.children[0])})"

    # --- Match ---
    def gen_match_stmt(self, node):
        subject = self.gen(node.children[0])
        cases = [c for c in node.children[1:] if isinstance(c, Tree) and c.data == "match_case"]
        lines = []
        for i, case in enumerate(cases):
            pattern = case.children[0]
            body = self.gen(case.children[1])
            if isinstance(pattern, Tree) and pattern.data == "match_wildcard":
                if i == 0:
                    lines.append(f"{self.ind()}if True:\n{body}")
                else:
                    lines.append(f"{self.ind()}else:\n{body}")
            else:
                val = self.gen(pattern)
                kw = "if" if i == 0 else "elif"
                lines.append(f"{self.ind()}{kw} {subject} == {val}:\n{body}")
        return "\n".join(lines)

    def gen_match_value(self, node):
        return self.gen(node.children[0])

    # --- Struct ---
    def gen_struct_def(self, node):
        name = str(node.children[0])
        fields_node = None
        for c in node.children[1:]:
            if isinstance(c, Tree) and c.data == "struct_fields":
                fields_node = c
                break

        if fields_node is None:
            lines = [f"{self.ind()}class {name}:"]
            self.indent += 1
            lines.append(f"{self.ind()}def __init__(self):")
            self.indent += 1
            lines.append(f"{self.ind()}pass")
            self.indent -= 1
            lines.append(f"{self.ind()}def __repr__(self):")
            self.indent += 1
            lines.append(f'{self.ind()}return "{name}()"')
            self.indent -= 2
            return "\n".join(lines)

        fields = []
        defaults = {}
        for c in fields_node.children:
            if isinstance(c, Tree) and c.data == "field_default":
                fname = str(c.children[0])
                fval = self.gen(c.children[1])
                fields.append(fname)
                defaults[fname] = fval
            elif isinstance(c, Tree) and c.data == "field_plain":
                fields.append(str(c.children[0]))
            elif isinstance(c, Token):
                fields.append(str(c))

        params = []
        for f in fields:
            if f in defaults:
                params.append(f"{f}={defaults[f]}")
            else:
                params.append(f)

        lines = [f"{self.ind()}class {name}:"]
        self.indent += 1
        lines.append(f"{self.ind()}def __init__(self, {', '.join(params)}):")
        self.indent += 1
        for f in fields:
            lines.append(f"{self.ind()}self.{f} = {f}")
        self.indent -= 1
        lines.append(f"{self.ind()}def __repr__(self):")
        self.indent += 1
        fmt = ", ".join(f"{f}={{self.{f}!r}}" for f in fields)
        lines.append(f'{self.ind()}return f"{name}({fmt})"')
        self.indent -= 1
        lines.append(f"{self.ind()}def __eq__(self, other):")
        self.indent += 1
        if fields:
            checks = " and ".join(f"self.{f} == other.{f}" for f in fields)
            lines.append(f"{self.ind()}return isinstance(other, {name}) and {checks}")
        else:
            lines.append(f"{self.ind()}return isinstance(other, {name})")
        self.indent -= 2
        return "\n".join(lines)

    def gen_struct_inherit(self, node):
        name = str(node.children[0])
        parent = str(node.children[1])
        fields_node = None
        for c in node.children[2:]:
            if isinstance(c, Tree) and c.data == "struct_fields":
                fields_node = c
                break

        fields = []
        defaults = {}
        if fields_node:
            for c in fields_node.children:
                if isinstance(c, Tree) and c.data == "field_default":
                    fname = str(c.children[0])
                    fields.append(fname)
                    defaults[fname] = self.gen(c.children[1])
                elif isinstance(c, Tree) and c.data == "field_plain":
                    fields.append(str(c.children[0]))
                elif isinstance(c, Token):
                    fields.append(str(c))

        params = []
        for f in fields:
            if f in defaults:
                params.append(f"{f}={defaults[f]}")
            else:
                params.append(f)

        lines = [f"{self.ind()}class {name}({parent}):"]
        self.indent += 1
        lines.append(f"{self.ind()}def __init__(self, *_parent_args, {', '.join(params)}, **_parent_kwargs):")
        self.indent += 1
        lines.append(f"{self.ind()}super().__init__(*_parent_args, **_parent_kwargs)")
        for f in fields:
            lines.append(f"{self.ind()}self.{f} = {f}")
        self.indent -= 2
        return "\n".join(lines)

    def gen_struct_fields(self, node):
        return ""

    def gen_field_plain(self, node):
        return str(node.children[0])

    def gen_field_default(self, node):
        return f"{node.children[0]}={self.gen(node.children[1])}"


# ============================================================
# プレリュード
# ============================================================
SMILE_PRELUDE = "from smile.stdlib import *\nimport smile.pypi_fetch as _pypi; _pypi.install()\n"


# ============================================================
# コンパイル・実行
# ============================================================
from smile.errors import format_runtime_error, analyze_syntax_error


def compile_smile(source, filename="<smile>"):
    parser = create_parser()
    try:
        tree = parser.parse(source)
    except Exception as e:
        err = analyze_syntax_error(e, source, filename)
        print(err.render())
        sys.exit(1)
    codegen = CodeGen()
    return codegen.gen(tree)


_PRELUDE_GLOBALS = None

def _get_prelude_globals():
    global _PRELUDE_GLOBALS
    if _PRELUDE_GLOBALS is not None:
        return _PRELUDE_GLOBALS
    globs = {}
    exec(compile(SMILE_PRELUDE, "<smile-prelude>", "exec"), globs)
    _PRELUDE_GLOBALS = globs
    return globs


def run_smile(source, filename="<smile>"):
    """コンパイルインタプリタ: .py生成 → 実行 → 自動削除"""
    import tempfile
    python_code = compile_smile(source, filename)
    full_code = SMILE_PRELUDE + python_code

    # 一時Pythonファイルに書き出し
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".py", prefix="smile_")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            f.write(full_code)

        # コンパイル (構文チェック+バイトコード化)
        code_obj = compile(full_code, filename, "exec")

        # 実行
        globs = dict(_get_prelude_globals())
        globs["__name__"] = "__main__"
        globs["__file__"] = filename
        exec(code_obj, globs)
    except SystemExit:
        raise
    except Exception as e:
        print(format_runtime_error(e, source, filename))
        sys.exit(1)
    finally:
        # 自動削除
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        # .pycも消す
        pyc = tmp_path + "c"
        if os.path.exists(pyc):
            try:
                os.unlink(pyc)
            except OSError:
                pass


# ============================================================
# .smile モジュールimport対応
# ============================================================
import importlib.abc
import importlib.machinery

class SmileModuleFinder(importlib.abc.MetaPathFinder):
    def find_module(self, fullname, path=None):
        parts = fullname.split(".")
        search_paths = path or [os.getcwd()]
        for base in search_paths:
            filepath = os.path.join(base, *parts) + ".smile"
            if os.path.exists(filepath):
                return SmileModuleLoader(filepath)
            dirpath = os.path.join(base, *parts)
            init_file = os.path.join(dirpath, "__init__.smile")
            if os.path.isdir(dirpath) and os.path.exists(init_file):
                return SmileModuleLoader(init_file)
        return None

class SmileModuleLoader(importlib.abc.Loader):
    def __init__(self, filepath):
        self.filepath = filepath

    def load_module(self, fullname):
        if fullname in sys.modules:
            return sys.modules[fullname]
        import types
        mod = types.ModuleType(fullname)
        mod.__file__ = self.filepath
        mod.__loader__ = self
        sys.modules[fullname] = mod
        source = Path(self.filepath).read_text(encoding="utf-8")
        python_code = compile_smile(source, self.filepath)
        full_code = SMILE_PRELUDE + python_code
        code_obj = compile(full_code, self.filepath, "exec")
        exec(code_obj, mod.__dict__)
        return mod

sys.meta_path.insert(0, SmileModuleFinder())


# ============================================================
# CLI
# ============================================================

def cmd_run(args):
    if not args:
        print("使い方: smile run <ファイル.smile>")
        sys.exit(1)
    filepath = args[0]
    if not os.path.exists(filepath):
        print(f"\n  ファイルが見つかりません: {filepath}")
        sys.exit(1)
    sys.argv = [filepath] + args[1:]
    source = Path(filepath).read_text(encoding="utf-8")
    run_smile(source, filepath)


def cmd_init(args):
    project_name = args[0] if args else os.path.basename(os.getcwd())
    project_dir = Path(args[0]) if args else Path(".")
    if args:
        project_dir.mkdir(exist_ok=True)

    main_file = project_dir / "main.smile"
    if not main_file.exists():
        main_file.write_text(
            '// ' + project_name + '\n\nprint("Hello from ' + project_name + '!")\n',
            encoding="utf-8"
        )

    config_file = project_dir / "smile.json"
    if not config_file.exists():
        config = {
            "name": project_name,
            "version": "0.1.0",
            "main": "main.smile",
            "description": "",
            "author": "",
        }
        config_file.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"プロジェクト「{project_name}」を初期化しました")
    if args:
        print(f"  cd {project_name}")
    print(f"  smile run main.smile")


def cmd_test(args):
    test_dir = Path(args[0]) if args else Path("tests")
    if not test_dir.exists():
        test_dir = Path(".")

    test_files = sorted(test_dir.glob("**/test_*.smile")) + sorted(test_dir.glob("**/*_test.smile"))
    if not test_files:
        print("テストファイルが見つかりません (test_*.smile または *_test.smile)")
        sys.exit(1)

    passed = 0
    failed = 0
    errors = []
    for tf in test_files:
        name = str(tf)
        try:
            source = tf.read_text(encoding="utf-8")
            python_code = compile_smile(source, str(tf))
            full_code = SMILE_PRELUDE + python_code
            code_obj = compile(full_code, str(tf), "exec")
            globs = dict(_get_prelude_globals())
            globs["__name__"] = "__test__"
            globs["__file__"] = str(tf)
            exec(code_obj, globs)
            print(f"  OK  {name}")
            passed += 1
        except SystemExit:
            raise
        except Exception as e:
            print(f"  NG  {name}: {e}")
            failed += 1
            errors.append((name, e))

    print(f"\n結果: {passed} 成功, {failed} 失敗 / {passed + failed} 件")
    if failed > 0:
        sys.exit(1)


LOGO = """
      0 0
       \\_/
      SMILE"""

def _setup_repl_completion(repl_globals):
    try:
        import readline
        keywords = [
            "if", "else", "while", "for", "in", "function", "return",
            "break", "continue", "import", "from", "as", "struct",
            "extends", "try", "catch", "finally", "throw", "match",
            "case", "async", "await", "true", "false", "none",
            "and", "or", "not", "print", "input_smile",
        ]
        def completer(text, state):
            options = [k for k in keywords if k.startswith(text)]
            options += [k for k in repl_globals if k.startswith(text) and not k.startswith("_")]
            if state < len(options):
                return options[state]
            return None
        readline.set_completer(completer)
        readline.parse_and_bind("tab: complete")
    except ImportError:
        pass

def cmd_repl():
    print(LOGO)
    print(f"  Smile Language v{VERSION} - Interpreter")
    print("  exit で終了 / Tabで補完")
    print("-" * 40)
    repl_globals = dict(_get_prelude_globals())
    repl_globals["__name__"] = "__repl__"
    _setup_repl_completion(repl_globals)
    while True:
        try:
            line = input("smile> ")
        except (EOFError, KeyboardInterrupt):
            print("\nバイバイ！")
            break
        if line.strip() in ("exit", "quit"):
            print("バイバイ！")
            break
        if not line.strip():
            continue
        try:
            python_code = compile_smile(line, "<repl>")
            try:
                result = eval(compile(python_code, "<repl>", "eval"), repl_globals)
                if result is not None:
                    print(result)
            except SyntaxError:
                exec(compile(python_code, "<repl>", "exec"), repl_globals)
        except SystemExit:
            break
        except Exception as e:
            print(format_runtime_error(e, line, "<repl>"))


def cmd_version():
    print(LOGO)
    print(f"  Smile Language v{VERSION}")
    print(f"  Python {sys.version}")
    print(f"  Platform: {sys.platform}")


def cmd_install(args):
    from smile.pypi_fetch import fetch_package
    if not args:
        print("使い方: smile install <パッケージ名>")
        print("  PyPIからパッケージを事前取得します (一時ファイル)")
        return
    for pkg in args:
        print(f"取得中: {pkg} ...", end=" ", flush=True)
        if fetch_package(pkg):
            print("OK (一時ファイル、終了後に自動削除)")
        else:
            print("失敗 (PyPIに見つかりません)")


def cmd_fmt(args):
    import re
    if not args:
        print("使い方: smile fmt <ファイル.smile> [--check]")
        return
    check_only = "--check" in args
    files = [a for a in args if not a.startswith("--")]
    dirty = 0
    for filepath in files:
        if not os.path.exists(filepath):
            print(f"ファイルが見つかりません: {filepath}")
            continue
        source = Path(filepath).read_text(encoding="utf-8")
        lines = source.split("\n")
        formatted = []
        for line in lines:
            stripped = line.rstrip()
            # normalize indent to 4 spaces
            leading = len(line) - len(line.lstrip())
            if line.strip():
                formatted.append(line[:leading] + line.strip())
            else:
                formatted.append("")
        result = "\n".join(formatted)
        if not result.endswith("\n"):
            result += "\n"
        if result != source:
            dirty += 1
            if check_only:
                print(f"  要修正  {filepath}")
            else:
                Path(filepath).write_text(result, encoding="utf-8")
                print(f"  整形済  {filepath}")
        else:
            print(f"  OK      {filepath}")
    if check_only and dirty > 0:
        sys.exit(1)


def cmd_help():
    print(LOGO)
    print(f"  Smile Language v{VERSION}")
    print()
    print("使い方:")
    print("  smile <ファイル.smile>        ファイルを実行")
    print("  smile run <ファイル.smile>    ファイルを実行 (引数渡し可)")
    print("  smile init [名前]             新しいプロジェクトを作成")
    print("  smile test [ディレクトリ]     テストを実行")
    print("  smile fmt <ファイル.smile>    コード整形")
    print("  smile debug <ファイル.smile>  ステップ実行デバッガー")
    print("  smile install <パッケージ>    PyPIから一時取得")
    print("  smile repl                    対話モード")
    print("  smile version                 バージョン表示")
    print("  smile help                    このヘルプ")
    print()
    print("  PyPIパッケージはimport時に自動取得、実行後に自動削除されます")


def main():
    if len(sys.argv) < 2:
        cmd_repl()
        return

    cmd = sys.argv[1]

    if cmd == "run":
        cmd_run(sys.argv[2:])
    elif cmd == "init":
        cmd_init(sys.argv[2:])
    elif cmd == "test":
        cmd_test(sys.argv[2:])
    elif cmd == "fmt":
        cmd_fmt(sys.argv[2:])
    elif cmd == "debug":
        if len(sys.argv) < 3:
            print("使い方: smile debug <ファイル.smile>")
            sys.exit(1)
        from smile.debugger import run_debug
        run_debug(sys.argv[2])
    elif cmd == "install":
        cmd_install(sys.argv[2:])
    elif cmd == "repl":
        cmd_repl()
    elif cmd == "version":
        cmd_version()
    elif cmd == "help":
        cmd_help()
    elif cmd.endswith(".smile"):
        sys.argv = sys.argv[1:]
        cmd_run([cmd] + sys.argv[1:])
    else:
        print(f"不明なコマンド: {cmd}")
        cmd_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
