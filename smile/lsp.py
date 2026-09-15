"""Smile Language LSP Server (簡易版)"""

import json
import sys
import re
from pathlib import Path


KEYWORDS = [
    "if", "else", "while", "for", "in", "function", "return",
    "break", "continue", "import", "from", "as", "struct",
    "extends", "try", "catch", "finally", "throw", "match",
    "case", "async", "await", "true", "false", "none",
    "and", "or", "not",
]

BUILTINS = [
    "print", "input_smile", "length", "to_string", "to_int",
    "to_float", "to_bool", "to_list", "sort", "reverse",
    "range", "map_list", "filter_list", "reduce_list",
    "sum_val", "min_val", "max_val", "abs_val",
    "read_file", "write_file", "json_parse", "json_stringify",
    "http_get", "http_post", "sleep", "now", "debug",
    "assert_true", "assert_equal",
]


def read_message(stream):
    headers = {}
    while True:
        line = stream.readline()
        if not line or line == b"\r\n":
            break
        key, val = line.decode("utf-8").strip().split(": ", 1)
        headers[key] = val
    length = int(headers.get("Content-Length", 0))
    if length == 0:
        return None
    body = stream.read(length)
    return json.loads(body.decode("utf-8"))


def send_message(stream, msg):
    body = json.dumps(msg).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n"
    stream.write(header.encode("utf-8"))
    stream.write(body)
    stream.flush()


def make_response(req_id, result):
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def get_diagnostics(uri, text):
    from smile.compiler import create_parser
    diagnostics = []
    try:
        parser = create_parser()
        parser.parse(text)
    except Exception as e:
        msg = str(e)
        line_match = re.search(r"line (\d+)", msg)
        line = int(line_match.group(1)) - 1 if line_match else 0
        diagnostics.append({
            "range": {
                "start": {"line": line, "character": 0},
                "end": {"line": line, "character": 100},
            },
            "severity": 1,
            "source": "smile",
            "message": f"構文エラー: {msg}",
        })
    return diagnostics


def get_completions(text, line, character):
    items = []
    for kw in KEYWORDS:
        items.append({"label": kw, "kind": 14, "detail": "キーワード"})
    for fn in BUILTINS:
        items.append({"label": fn, "kind": 3, "detail": "組み込み関数"})
    # extract user-defined names
    for m in re.finditer(r'\b(?:function|struct)\s+([a-zA-Z_぀-鿿]\w*)', text):
        items.append({"label": m.group(1), "kind": 3, "detail": "ユーザー定義"})
    for m in re.finditer(r'^([a-zA-Z_぀-鿿]\w*)\s*=', text, re.MULTILINE):
        items.append({"label": m.group(1), "kind": 6, "detail": "変数"})
    return items


def get_hover(text, line, character):
    lines = text.split("\n")
    if line >= len(lines):
        return None
    current = lines[line]
    # find word at position
    word = ""
    start = character
    while start > 0 and (current[start-1].isalnum() or current[start-1] == "_"):
        start -= 1
    end = character
    while end < len(current) and (current[end].isalnum() or current[end] == "_"):
        end += 1
    word = current[start:end]
    if not word:
        return None

    docs = {
        "function": "関数を定義します\n```\nfunction 名前(引数) { ... }\n```",
        "struct": "構造体を定義します\n```\nstruct 名前 { フィールド }\n```",
        "match": "値のパターンマッチング\n```\nmatch 値 {\n  case パターン { ... }\n}\n```",
        "async": "非同期関数を定義します\n```\nasync function 名前() { ... }\n```",
        "await": "非同期処理の完了を待ちます",
        "print": "値をコンソールに表示します",
        "length": "リストや文字列の長さを返します",
    }
    if word in docs:
        return {"contents": {"kind": "markdown", "value": docs[word]}}
    if word in KEYWORDS:
        return {"contents": {"kind": "plaintext", "value": f"Smileキーワード: {word}"}}
    if word in BUILTINS:
        return {"contents": {"kind": "plaintext", "value": f"組み込み関数: {word}()"}}
    return None


def run_lsp():
    documents = {}
    stdin = sys.stdin.buffer
    stdout = sys.stdout.buffer

    while True:
        msg = read_message(stdin)
        if msg is None:
            break

        method = msg.get("method", "")
        params = msg.get("params", {})
        req_id = msg.get("id")

        if method == "initialize":
            result = {
                "capabilities": {
                    "textDocumentSync": 1,
                    "completionProvider": {"triggerCharacters": ["."]},
                    "hoverProvider": True,
                    "diagnosticProvider": {"interFileDependencies": False, "workspaceDiagnostics": False},
                },
                "serverInfo": {"name": "smile-lsp", "version": "0.3.0"},
            }
            send_message(stdout, make_response(req_id, result))

        elif method == "initialized":
            pass

        elif method == "shutdown":
            send_message(stdout, make_response(req_id, None))

        elif method == "exit":
            break

        elif method == "textDocument/didOpen":
            uri = params["textDocument"]["uri"]
            text = params["textDocument"]["text"]
            documents[uri] = text
            diags = get_diagnostics(uri, text)
            send_message(stdout, {
                "jsonrpc": "2.0",
                "method": "textDocument/publishDiagnostics",
                "params": {"uri": uri, "diagnostics": diags},
            })

        elif method == "textDocument/didChange":
            uri = params["textDocument"]["uri"]
            for change in params.get("contentChanges", []):
                documents[uri] = change["text"]
            text = documents[uri]
            diags = get_diagnostics(uri, text)
            send_message(stdout, {
                "jsonrpc": "2.0",
                "method": "textDocument/publishDiagnostics",
                "params": {"uri": uri, "diagnostics": diags},
            })

        elif method == "textDocument/completion":
            uri = params["textDocument"]["uri"]
            text = documents.get(uri, "")
            pos = params["position"]
            items = get_completions(text, pos["line"], pos["character"])
            send_message(stdout, make_response(req_id, items))

        elif method == "textDocument/hover":
            uri = params["textDocument"]["uri"]
            text = documents.get(uri, "")
            pos = params["position"]
            hover = get_hover(text, pos["line"], pos["character"])
            send_message(stdout, make_response(req_id, hover))

        elif req_id is not None:
            send_message(stdout, make_response(req_id, None))


if __name__ == "__main__":
    run_lsp()
