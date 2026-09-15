"""Smile Language - 超詳細エラーメッセージシステム"""

import sys
import re
import difflib
import traceback


# Smileのビルトイン名一覧（typo検出用）
def _get_builtin_names():
    try:
        from smile.stdlib import EXPORTS
        return list(EXPORTS.keys()) + ["print", "True", "False", "None", "true", "false", "none"]
    except Exception:
        return ["print", "length", "to_string", "to_int", "to_float", "input_smile", "range_smile"]

BUILTIN_NAMES = _get_builtin_names()


def find_similar(name, candidates, n=3, cutoff=0.5):
    """似ている名前を探す"""
    return difflib.get_close_matches(name, candidates, n=n, cutoff=cutoff)


def get_smile_line(source_lines, python_lineno, line_map=None):
    """Pythonの行番号からSmileのソース行を特定"""
    if line_map and python_lineno in line_map:
        return line_map[python_lineno]
    return None


class SmileError:
    """エラー情報を構造化して保持"""
    def __init__(self):
        self.title = ""
        self.what = ""
        self.where_file = ""
        self.where_line = 0
        self.source_line = ""
        self.arrow_col = -1
        self.arrow_len = 1
        self.why = ""
        self.how_to_fix = []
        self.example_before = ""
        self.example_after = ""
        self.note = ""

    def render(self):
        """エラーをきれいに表示"""
        lines = []
        width = 60

        lines.append("")
        lines.append("=" * width)
        lines.append(f"  SMILE ERROR: {self.title}")
        lines.append("=" * width)
        lines.append("")

        # 何が起きた？
        lines.append(f"  [何が起きた？]")
        lines.append(f"    {self.what}")
        lines.append("")

        # どこで？
        if self.where_file or self.where_line:
            lines.append(f"  [どこで？]")
            if self.where_file:
                lines.append(f"    ファイル: {self.where_file}")
            if self.where_line > 0:
                lines.append(f"    行: {self.where_line}")
            lines.append("")

        # ソースコード表示
        if self.source_line:
            lines.append(f"  [コード]")
            # 前後の行も含めて表示
            lines.append(f"    {self.where_line} | {self.source_line}")
            if self.arrow_col >= 0:
                padding = " " * (self.arrow_col + len(str(self.where_line)) + 4)
                arrows = "^" * max(self.arrow_len, 1)
                lines.append(f"    {' ' * len(str(self.where_line))}   {' ' * self.arrow_col}{arrows} ここ")
            lines.append("")

        # なぜ？
        if self.why:
            lines.append(f"  [なぜ？]")
            lines.append(f"    {self.why}")
            lines.append("")

        # 直し方
        if self.how_to_fix:
            lines.append(f"  [こうすれば直せます]")
            for i, fix in enumerate(self.how_to_fix, 1):
                lines.append(f"    {i}. {fix}")
            lines.append("")

        # 修正例
        if self.example_before or self.example_after:
            lines.append(f"  [修正例]")
            if self.example_before:
                for i, l in enumerate(self.example_before.split("\n")):
                    lines.append(f"    {'修正前: ' if i == 0 else '         '}{l}")
            if self.example_after:
                for i, l in enumerate(self.example_after.split("\n")):
                    lines.append(f"    {'修正後: ' if i == 0 else '         '}{l}")
            lines.append("")

        # 補足
        if self.note:
            lines.append(f"  [補足]")
            lines.append(f"    {self.note}")
            lines.append("")

        lines.append("-" * width)
        lines.append("")

        return "\n".join(lines)


def analyze_name_error(exc, source_lines, user_vars, filename):
    """NameErrorを詳細に分析"""
    err = SmileError()
    err.title = "名前が見つからない"
    err.where_file = filename

    m = re.search(r"name '(\w+)' is not defined", str(exc))
    name = m.group(1) if m else "?"

    err.what = f"「{name}」という名前が使われていますが、定義されていません。"

    # 行番号を取得
    tb = exc.__traceback__
    while tb.tb_next:
        tb = tb.tb_next
    py_line = tb.tb_lineno

    # ソース行のマッピングを推測
    smile_line = _find_smile_source_line(name, source_lines)
    if smile_line:
        err.where_line = smile_line[0]
        err.source_line = smile_line[1]
        col = smile_line[1].find(name)
        if col >= 0:
            err.arrow_col = col
            err.arrow_len = len(name)

    # 似ている名前を探す
    all_names = list(user_vars) + BUILTIN_NAMES
    similar = find_similar(name, all_names)

    if similar:
        err.why = f"「{name}」に似た名前があります: {', '.join(similar)}"
        err.how_to_fix.append(f"もしかして「{similar[0]}」のことですか？")
        err.example_before = f'{name}(...)'
        err.example_after = f'{similar[0]}(...)'
    else:
        err.why = "この名前は定義されていません。使う前に変数や関数を定義する必要があります。"
        err.how_to_fix.append(f"変数なら先に代入してください: {name} = 値")
        err.how_to_fix.append(f"関数なら先に定義してください: function {name}(...) {{ ... }}")
        err.example_before = f'print({name})'
        err.example_after = f'{name} = "何か"\nprint({name})'

    # よくある間違いパターン
    if name == "len":
        err.how_to_fix.insert(0, "Smileでは len() の代わりに length() を使います。")
        err.example_after = f'length(リスト)'
    elif name == "str":
        err.how_to_fix.insert(0, "Smileでは str() の代わりに to_string() を使います。")
        err.example_after = f'to_string(値)'
    elif name == "int":
        err.how_to_fix.insert(0, "Smileでは int() の代わりに to_int() を使います。")
        err.example_after = f'to_int(値)'
    elif name == "float":
        err.how_to_fix.insert(0, "Smileでは float() の代わりに to_float() を使います。")
        err.example_after = f'to_float(値)'
    elif name == "input":
        err.how_to_fix.insert(0, "Smileでは input() の代わりに input_smile() を使います。")
        err.example_after = f'input_smile("質問: ")'
    elif name == "range":
        err.how_to_fix.insert(0, "Smileでは range() の代わりに range_smile() を使います。")
        err.example_after = f'range_smile(1, 10)'
    elif name == "map":
        err.how_to_fix.insert(0, "Smileでは map() の代わりに map_list() を使います。")
    elif name == "filter":
        err.how_to_fix.insert(0, "Smileでは filter() の代わりに filter_list() を使います。")
    elif name == "abs":
        err.how_to_fix.insert(0, "Smileでは abs() の代わりに abs_val() を使います。")
    elif name == "max":
        err.how_to_fix.insert(0, "Smileでは max() の代わりに max_val() を使います。")
    elif name == "min":
        err.how_to_fix.insert(0, "Smileでは min() の代わりに min_val() を使います。")
    elif name == "sum":
        err.how_to_fix.insert(0, "Smileでは sum() の代わりに sum_val() を使います。")
    elif name == "round":
        err.how_to_fix.insert(0, "Smileでは round() の代わりに round_val() を使います。")

    return err


def analyze_type_error(exc, source_lines, filename):
    """TypeErrorを詳細に分析"""
    err = SmileError()
    err.title = "型が合わない"
    err.where_file = filename
    msg = str(exc)

    tb = exc.__traceback__
    while tb.tb_next:
        tb = tb.tb_next
    err.where_line = 0

    if "unsupported operand type" in msg:
        m = re.search(r"unsupported operand type\(s\) for (.+): '(\w+)' and '(\w+)'", msg)
        if m:
            op, t1, t2 = m.group(1), m.group(2), m.group(3)
            err.what = f"「{t1}」型と「{t2}」型を「{op}」で計算しようとしました。"
            err.why = f"違う型同士は直接 {op} できません。"
            if "str" in (t1, t2) and "int" in (t1, t2):
                err.how_to_fix.append("文字列と数値を結合するには、数値を to_string() で変換してください。")
                err.example_before = '"年齢: " + 25'
                err.example_after = '"年齢: " + to_string(25)'
            elif "str" in (t1, t2) and "float" in (t1, t2):
                err.how_to_fix.append("文字列と小数を結合するには、小数を to_string() で変換してください。")
                err.example_before = '"体重: " + 65.5'
                err.example_after = '"体重: " + to_string(65.5)'
            else:
                err.how_to_fix.append(f"to_string(), to_int(), to_float() で型を変換してください。")
        else:
            err.what = f"型が合っていません: {msg}"
            err.how_to_fix.append("型変換関数を使ってみてください: to_string(), to_int(), to_float()")

    elif "can only concatenate str" in msg:
        err.what = "文字列と別の型を + で結合しようとしました。"
        err.why = "文字列に足せるのは文字列だけです。"
        err.how_to_fix.append("数値を to_string() で文字列に変換してから結合してください。")
        err.example_before = '"結果: " + 42'
        err.example_after = '"結果: " + to_string(42)'

    elif "not callable" in msg:
        m = re.search(r"'(\w+)' object is not callable", msg)
        typename = m.group(1) if m else "?"
        err.what = f"「{typename}」型の値を関数のように呼び出そうとしました。"
        err.why = "関数ではないものに () を付けて呼び出しています。"
        err.how_to_fix.append("変数名と関数名が被っていないか確認してください。")
        err.how_to_fix.append("同じ名前の変数に値を入れると、関数が上書きされます。")
        err.example_before = 'length = 5\nprint(length([1,2,3]))'
        err.example_after = 'my_length = 5\nprint(length([1,2,3]))'

    elif "argument" in msg:
        m = re.search(r"(\w+)\(\) takes (\d+) .+ (\d+) .+ given", msg)
        if m:
            fname, expected, got = m.group(1), m.group(2), m.group(3)
            err.what = f"関数「{fname}」に渡した引数の数が間違っています。"
            err.why = f"必要な引数: {expected}個、渡された引数: {got}個"
            err.how_to_fix.append(f"「{fname}」に渡す引数の数を{expected}個にしてください。")
        else:
            err.what = f"関数の引数が正しくありません: {msg}"
            err.how_to_fix.append("関数に渡す引数の数や型を確認してください。")

    elif "indices must be integers" in msg:
        err.what = "リストのインデックスに整数以外を使おうとしました。"
        err.why = "リストの要素にアクセスするには整数が必要です。"
        err.how_to_fix.append("to_int() で整数に変換してからアクセスしてください。")
        err.example_before = 'list[1.5]'
        err.example_after = 'list[to_int(1.5)]'

    else:
        err.what = f"型エラー: {msg}"
        err.how_to_fix.append("型変換関数を使ってみてください: to_string(), to_int(), to_float()")

    return err


def analyze_index_error(exc, source_lines, filename):
    """IndexErrorを詳細に分析"""
    err = SmileError()
    err.title = "リストの範囲外アクセス"
    err.where_file = filename

    err.what = "リストの存在しない位置にアクセスしようとしました。"
    err.why = (
        "リストのインデックスは 0 から始まります。\n"
        "    例えば、要素が3つのリストは [0], [1], [2] でアクセスします。\n"
        "    [3] 以上を使うとこのエラーになります。"
    )
    err.how_to_fix.append("length() でリストの長さを確認しましょう。")
    err.how_to_fix.append("最後の要素は list[length(list) - 1] でアクセスできます。")
    err.how_to_fix.append("安全にアクセスするには、先にインデックスを確認しましょう。")
    err.example_before = 'items = ["a", "b", "c"]\nprint(items[5])'
    err.example_after = (
        'items = ["a", "b", "c"]\n'
        'if 5 < length(items) {\n'
        '    print(items[5])\n'
        '} else {\n'
        '    print("その位置には要素がありません")\n'
        '}'
    )

    return err


def analyze_key_error(exc, source_lines, filename):
    """KeyErrorを詳細に分析"""
    err = SmileError()
    err.title = "辞書のキーが見つからない"
    err.where_file = filename

    key = str(exc).strip("'\"")
    err.what = f"辞書に「{key}」というキーがありません。"
    err.why = "存在しないキーで辞書にアクセスしようとしました。"
    err.how_to_fix.append(f"keys() で辞書のキー一覧を確認しましょう。")
    err.how_to_fix.append(f"contains(辞書, \"{key}\") でキーの存在を確認できます。")
    err.example_before = f'data = {{"name": "太郎"}}\nprint(data["{key}"])'
    err.example_after = (
        f'data = {{"name": "太郎"}}\n'
        f'if contains(data, "{key}") {{\n'
        f'    print(data["{key}"])\n'
        f'}} else {{\n'
        f'    print("キーが見つかりません")\n'
        f'}}'
    )

    return err


def analyze_zero_division(exc, source_lines, filename):
    """ZeroDivisionErrorを詳細に分析"""
    err = SmileError()
    err.title = "0で割り算しようとした"
    err.where_file = filename

    err.what = "0で割り算をしようとしました。数学的に0で割ることはできません。"
    err.why = "割る数 (/ の右側) が 0 になっています。"
    err.how_to_fix.append("割る数が0でないか確認してから割り算してください。")
    err.how_to_fix.append("0の場合の処理を別に書きましょう。")
    err.example_before = 'result = total / count'
    err.example_after = (
        'if count != 0 {\n'
        '    result = total / count\n'
        '} else {\n'
        '    print("0で割れません")\n'
        '    result = 0\n'
        '}'
    )

    return err


def analyze_attribute_error(exc, source_lines, filename):
    """AttributeErrorを詳細に分析"""
    err = SmileError()
    err.title = "存在しない属性・メソッド"
    err.where_file = filename

    msg = str(exc)
    m = re.search(r"'(\w+)' object has no attribute '(\w+)'", msg)
    if m:
        typename, attr = m.group(1), m.group(2)
        err.what = f"「{typename}」型には「{attr}」という属性やメソッドがありません。"
        err.why = f"「{typename}」型の値に .{attr} を使おうとしましたが、そのような機能はありません。"

        if typename == "str":
            str_methods = ["split", "strip", "upper", "lower", "replace", "startswith", "endswith", "find", "count"]
            similar = find_similar(attr, str_methods)
            if similar:
                err.how_to_fix.append(f"もしかして .{similar[0]}() のことですか？")
            err.how_to_fix.append("文字列で使えるメソッド: " + ", ".join(str_methods))
        elif typename == "list":
            list_methods = ["append", "pop", "sort", "reverse", "index", "count", "clear", "copy"]
            similar = find_similar(attr, list_methods)
            if similar:
                err.how_to_fix.append(f"もしかして .{similar[0]}() のことですか？")
            err.how_to_fix.append("Smileのリスト関数: push(), pop(), sort(), length(), contains()")
        elif typename == "dict":
            err.how_to_fix.append("Smileの辞書関数: keys(), values(), contains()")
        elif typename == "NoneType":
            err.what = f"「none」(値なし) に .{attr} を使おうとしました。"
            err.why = "変数の値が none になっています。関数が値を返していない可能性があります。"
            err.how_to_fix.append("関数に return 文があるか確認してください。")
            err.how_to_fix.append("none チェックを入れましょう。")
            err.example_after = f'if result != none {{\n    print(result.{attr})\n}}'
        else:
            err.how_to_fix.append(f"「{typename}」が持つ属性を確認してください。")
            err.how_to_fix.append("structで定義したフィールド名を見直してみてください。")
    else:
        err.what = f"属性エラー: {msg}"
        err.how_to_fix.append("オブジェクトの型と属性名を確認してください。")

    return err


def analyze_value_error(exc, source_lines, filename):
    """ValueErrorを詳細に分析"""
    err = SmileError()
    err.title = "値が正しくない"
    err.where_file = filename
    msg = str(exc)

    if "invalid literal for int()" in msg:
        m = re.search(r"invalid literal for int\(\) with base \d+: '(.+)'", msg)
        val = m.group(1) if m else "?"
        err.what = f"「{val}」を整数に変換しようとしましたが、整数ではありません。"
        err.why = f"to_int() に渡せるのは \"123\" のような数字だけの文字列です。"
        err.how_to_fix.append("文字列が数字だけで構成されているか確認してください。")
        err.how_to_fix.append("小数の文字列なら、先に to_float() してから to_int() してください。")
        err.example_before = f'to_int("{val}")'
        err.example_after = f'to_int(to_float("{val}"))  // 小数の場合\n// または数字以外を取り除いてから変換'
    elif "could not convert string to float" in msg:
        err.what = "文字列を小数に変換できませんでした。"
        err.how_to_fix.append("文字列が数値として正しいか確認してください。")
    else:
        err.what = f"値が正しくありません: {msg}"
        err.how_to_fix.append("渡している値が期待される形式か確認してください。")

    return err


def analyze_file_error(exc, source_lines, filename):
    """FileNotFoundErrorを詳細に分析"""
    err = SmileError()
    err.title = "ファイルが見つからない"
    err.where_file = filename

    m = re.search(r"No such file or directory: '(.+)'", str(exc))
    filepath = m.group(1) if m else str(exc)

    err.what = f"ファイル「{filepath}」が見つかりません。"
    err.why = "指定されたパスにファイルが存在しません。"
    err.how_to_fix.append("ファイル名のスペルを確認してください。")
    err.how_to_fix.append("ファイルパスが正しいか確認してください。")
    err.how_to_fix.append("ファイルの拡張子（.txt, .smile など）を忘れていませんか？")
    err.note = (
        "パスの区切りは「/」を使えます。\n"
        '    例: read_file("data/names.txt")'
    )

    return err


def analyze_recursion_error(exc, source_lines, filename):
    """RecursionErrorを詳細に分析"""
    err = SmileError()
    err.title = "再帰が深すぎる"
    err.where_file = filename

    err.what = "関数が自分自身を呼び出しすぎて、限界に達しました。"
    err.why = (
        "再帰（関数が自分自身を呼ぶこと）に終了条件がないか、\n"
        "    終了条件が正しく機能していない可能性があります。"
    )
    err.how_to_fix.append("再帰関数に終了条件 (if文で return する部分) があるか確認してください。")
    err.how_to_fix.append("終了条件が確実に到達されるか確認してください。")
    err.how_to_fix.append("再帰の代わりに while ループを使うことも検討してください。")
    err.example_before = (
        '// 終了条件がない！\n'
        'function countdown(n) {\n'
        '    print(to_string(n))\n'
        '    countdown(n - 1)\n'
        '}'
    )
    err.example_after = (
        '// 終了条件あり\n'
        'function countdown(n) {\n'
        '    if n <= 0 {\n'
        '        print("終了！")\n'
        '        return\n'
        '    }\n'
        '    print(to_string(n))\n'
        '    countdown(n - 1)\n'
        '}'
    )

    return err


def analyze_overflow_error(exc, source_lines, filename):
    """OverflowErrorを詳細に分析"""
    err = SmileError()
    err.title = "数値が大きすぎる"
    err.where_file = filename

    err.what = "計算結果の数値が大きすぎて処理できません。"
    err.why = "コンピュータが扱える数値には限界があります。"
    err.how_to_fix.append("計算式を見直して、数値が大きくなりすぎないようにしてください。")
    err.how_to_fix.append("途中で割り算やmodを使って値を抑えることも検討してください。")

    return err


def _find_smile_source_line(name, source_lines):
    """ソースコードから名前が使われている行を見つける"""
    for i, line in enumerate(source_lines, 1):
        stripped = line.strip()
        if stripped.startswith("//"):
            continue
        if name in stripped:
            return (i, stripped)
    return None


def _find_source_context(source_lines, lineno, context=2):
    """ソースコードの前後context行を取得"""
    result = []
    start = max(0, lineno - context - 1)
    end = min(len(source_lines), lineno + context)
    for i in range(start, end):
        marker = " >> " if i == lineno - 1 else "    "
        result.append(f"  {marker}{i+1:4d} | {source_lines[i]}")
    return "\n".join(result)


def analyze_syntax_error(e, source, filename):
    """パース段階のSyntaxErrorを詳細に分析"""
    err = SmileError()
    err.title = "書き方が間違っている"
    err.where_file = filename

    line = getattr(e, 'line', None)
    col = getattr(e, 'column', None)

    if line:
        err.where_line = line
        source_lines = source.split("\n")
        if 0 < line <= len(source_lines):
            err.source_line = source_lines[line - 1]
            if col:
                err.arrow_col = col - 1
                err.arrow_len = 1

    msg = str(e)

    # よくあるパターンを検出
    if err.source_line:
        sl = err.source_line.strip()

        if sl.count("(") != sl.count(")"):
            err.what = "括弧 () の数が合っていません。"
            opening = sl.count("(")
            closing = sl.count(")")
            if opening > closing:
                err.why = f"「(」が{opening}個、「)」が{closing}個です。閉じ括弧が足りません。"
                err.how_to_fix.append("閉じ括弧 ) を追加してください。")
            else:
                err.why = f"「(」が{opening}個、「)」が{closing}個です。開き括弧が足りません。"
                err.how_to_fix.append("開き括弧 ( を追加してください。")

        elif sl.count("{") != sl.count("}"):
            err.what = "波括弧 {} の数が合っていません。"
            err.how_to_fix.append("ブロック { ... } が正しく閉じているか確認してください。")

        elif sl.count("[") != sl.count("]"):
            err.what = "角括弧 [] の数が合っていません。"
            err.how_to_fix.append("リスト [ ... ] が正しく閉じているか確認してください。")

        elif "if " in sl and "{" not in sl:
            err.what = "if文にブロック { } がありません。"
            err.why = "Smileでは if文の本体を { } で囲む必要があります。"
            err.how_to_fix.append("if の条件の後に { ... } を追加してください。")
            err.example_before = "if x > 0\n    print(x)"
            err.example_after = 'if x > 0 {\n    print(to_string(x))\n}'

        elif "while " in sl and "{" not in sl:
            err.what = "while文にブロック { } がありません。"
            err.how_to_fix.append("while の条件の後に { ... } を追加してください。")

        elif "for " in sl and "{" not in sl:
            err.what = "for文にブロック { } がありません。"
            err.how_to_fix.append("for ... in ... の後に { ... } を追加してください。")

        elif "function " in sl and "{" not in sl:
            err.what = "function定義にブロック { } がありません。"
            err.how_to_fix.append("function の引数の後に { ... } を追加してください。")

        elif "def " in sl:
            err.what = "Smileでは「def」ではなく「function」を使います。"
            err.how_to_fix.append("「def」を「function」に変えてください。")
            err.example_before = "def add(a, b) { return a + b }"
            err.example_after = "function add(a, b) { return a + b }"

        elif ": " in sl and not any(sl.startswith(kw) for kw in ["struct", "//"]):
            if "if " in sl or "for " in sl or "while " in sl:
                err.what = "Smileでは : (コロン) ではなく { } (波括弧) を使います。"
                err.why = "PythonやRubyと違い、Smileはブロックを { } で囲みます。"
                err.how_to_fix.append(": を消して { } を使ってください。")

        elif sl.endswith(";"):
            err.what = "Smileではセミコロン ; は不要です。"
            err.how_to_fix.append("行末の ; を消してください。")
            err.note = "SmileではPythonのように、行末に何もつけなくてOKです。"

        else:
            err.what = f"この行の書き方に間違いがあります。"
            err.how_to_fix.append("括弧 (), {}, [] の対応を確認してください。")
            err.how_to_fix.append("予約語(if, for, while, function, struct)のスペルを確認してください。")
            err.how_to_fix.append("文字列の引用符 \" \" が閉じているか確認してください。")
    else:
        err.what = f"構文エラーが発生しました。"
        err.how_to_fix.append("コード全体で括弧の対応を確認してください。")

    # ソースコードのコンテキスト表示
    if line and source:
        source_lines = source.split("\n")
        ctx = _find_source_context(source_lines, line)
        if ctx:
            err.note = (err.note + "\n\n" if err.note else "") + "  周辺のコード:\n" + ctx

    return err


def format_runtime_error(exc, source, filename="<smile>"):
    """実行時エラーを超詳細に分析して表示"""
    source_lines = source.split("\n") if source else []
    etype = type(exc).__name__

    # exec時のグローバル変数名を取得（user_varsとして使う）
    user_vars = set()
    for line in source_lines:
        line = line.strip()
        m = re.match(r'^(\w+)\s*=', line)
        if m:
            user_vars.add(m.group(1))
        m = re.match(r'^function\s+(\w+)', line)
        if m:
            user_vars.add(m.group(1))

    if etype == "NameError":
        err = analyze_name_error(exc, source_lines, user_vars, filename)
    elif etype == "TypeError":
        err = analyze_type_error(exc, source_lines, filename)
    elif etype == "IndexError":
        err = analyze_index_error(exc, source_lines, filename)
    elif etype == "KeyError":
        err = analyze_key_error(exc, source_lines, filename)
    elif etype == "ZeroDivisionError":
        err = analyze_zero_division(exc, source_lines, filename)
    elif etype == "AttributeError":
        err = analyze_attribute_error(exc, source_lines, filename)
    elif etype == "ValueError":
        err = analyze_value_error(exc, source_lines, filename)
    elif etype == "FileNotFoundError":
        err = analyze_file_error(exc, source_lines, filename)
    elif etype == "RecursionError":
        err = analyze_recursion_error(exc, source_lines, filename)
    elif etype == "OverflowError":
        err = analyze_overflow_error(exc, source_lines, filename)
    else:
        err = SmileError()
        err.title = etype
        err.where_file = filename
        err.what = str(exc)
        err.how_to_fix.append("エラーメッセージを読んで、コードを見直してみてください。")

    # トレースバックからスマイル側の行を推定
    if hasattr(exc, "__traceback__") and exc.__traceback__ and not err.source_line:
        tb = exc.__traceback__
        while tb.tb_next:
            tb = tb.tb_next
        py_line = tb.tb_lineno

        # Preludeの行数を引いてSmileの行を推測（おおよそ）
        # 正確なマッピングはline_mapで行うが、ない場合は推定
        if err.where_line == 0 and source_lines:
            # エラーメッセージから手がかりを探す
            msg = str(exc)
            for pattern_name in re.findall(r"'(\w+)'", msg):
                found = _find_smile_source_line(pattern_name, source_lines)
                if found:
                    err.where_line = found[0]
                    err.source_line = found[1]
                    col = found[1].find(pattern_name)
                    if col >= 0:
                        err.arrow_col = col
                        err.arrow_len = len(pattern_name)
                    break

    return err.render()
