```
  0 0
  \_/
  SMILE
```

# Smile言語

**軽くて、安全で、エラーメッセージが優しいプログラミング言語**

何でも作りたい。でも作る知識がない。そんな人のための言語。

## 特徴

- **読みやすい構文** - 省略なし、全部読める
- **超詳細なエラーメッセージ** - 日本語で何が間違っているか、どう直すか教えてくれる
- **高速実行** - コンパイルインタプリタ方式（内部でPythonに変換→実行→自動削除）
- **pip不要のパッケージ取得** - importするだけでPyPIから自動ダウンロード、終わったら自動削除
- **Pythonの全ライブラリが使える** - pipで入れたものもそのまま使える
- **豊富な標準ライブラリ** - 80以上の関数がimport不要で使える
- **match文** - パターンマッチングで分岐をすっきり
- **async/await** - 非同期処理もシンプルに
- **Webフレームワーク内蔵** - Flask風のルーティングですぐにWebアプリ
- **デバッガー** - ステップ実行で動きを確認
- **VS Code対応** - シンタックスハイライト＋LSP
- **低レイヤーアクセス** - BIOS/SMBIOS/ACPI読み取り、メモリ操作、アセンブラも安全に

## インストール

```bash
pip install lark
```

リポジトリをクローンして使う:

```bash
git clone https://github.com/okmaikura-maker/smile-lang.git
cd smile-lang
python -m smile
```

## はじめてのSmile

```
// hello.smile
print("こんにちは、Smile言語!")

name = input_smile("名前は？ > ")
print("いい名前だね、" + name + "さん!")

// リスト操作
numbers = [1, 2, 3, 4, 5]
doubled = map_list(|n| n * 2, numbers)
print("2倍: " + to_string(doubled))
```

```bash
python -m smile hello.smile
```

## 構文

### 変数と型

```
x = 42
name = "太郎"
pi = 3.14
active = true
items = [1, 2, 3]
config = {"key": "value"}
```

### 関数

```
function greet(name, greeting="こんにちは") {
    return greeting + "、" + name + "さん!"
}

print(greet("太郎"))
print(greet("花子", "おはよう"))

// 可変長引数
function sum_all(*nums) {
    return sum_val(nums)
}

// 型アノテーション（ドキュメント用）
function add(a: int, b: int) -> int {
    return a + b
}
```

### 条件分岐

```
score = 85
if score >= 90 {
    print("Aランク!")
} else if score >= 70 {
    print("Bランク!")
} else {
    print("がんばろう!")
}

// 三項演算子
status = "大人" if age >= 18 else "子供"
```

### match文

```
x = 3
match x {
    case 1 {
        print("1です")
    }
    case 2 {
        print("2です")
    }
    case _ {
        print("その他")
    }
}
```

### ループ

```
for item in items {
    print(item)
}

for i, name in enumerate_list(names) {
    print(to_string(i) + ": " + name)
}

while condition {
    // ...
}
```

### async/await

```
import asyncio

async function fetch_data(url: string) -> string {
    await asyncio.sleep(1)
    return "データ取得完了"
}

async function main() {
    result = await fetch_data("https://example.com")
    print(result)
}
asyncio.run(main())
```

### try/catch

```
try {
    result = 10 / 0
} catch e {
    print("エラー: " + to_string(e))
} finally {
    print("完了")
}
```

### 構造体

```
struct Player {
    name
    level = 1
    hp = 100
}

struct Hero extends Player {
    skill = "none"
}

p = Player("勇者", level=5)
h = Hero("魔法使い", level=3, skill="ファイア")
```

### f-string / パイプ / リスト内包表記

```
name = "World"
print(f"Hello, {name}!")

result = [3, 1, 4, 1, 5] |> sort |> reverse

squares = [x ** 2 for x in range(10)]
evens = [x for x in range(20) if x % 2 == 0]
```

### PyPIパッケージの自動取得

```
// pip installしていなくても自動でPyPIから取得
// 実行後に自動削除される
import art
print(art.text2art("Smile"))
```

### Webフレームワーク

```
from smile.web import create_app

app = create_app("MyApp")

@app.get("/")
function index(req, res) {
    res.html("<h1>こんにちは!</h1>")
}

@app.get("/api/data")
function api_data(req, res) {
    res.json({"message": "Hello from Smile!"})
}

app.run(port=8080)
```

## CLIコマンド

```
smile <ファイル.smile>        ファイルを実行
smile run <ファイル.smile>    ファイルを実行 (引数渡し可)
smile init [名前]             新しいプロジェクトを作成
smile test [ディレクトリ]     テストを実行
smile fmt <ファイル.smile>    コード整形
smile debug <ファイル.smile>  ステップ実行デバッガー
smile install <パッケージ>    PyPIから一時取得
smile repl                    対話モード (Tab補完対応)
smile version                 バージョン表示
smile help                    ヘルプ
```

## エラーメッセージ

Smileのエラーメッセージは日本語で詳細に教えてくれる:

```
============================================================
  SMILE ERROR: NameError
============================================================

  [何が起きた？]
    'prnt' という名前は見つかりません

  [どこで？]
    ファイル: hello.smile
    行: 3

  [コード]
    3 | prnt("hello")
        ^^^^ ここ

  [もしかして？]
    → print

  [こうすれば直せます]
    1. 'prnt' を 'print' に変更してみてください
    2. スペルミスがないか確認してください

------------------------------------------------------------
```

対応エラー: NameError, TypeError, IndexError, KeyError, ZeroDivisionError, AttributeError, ValueError, FileNotFoundError, RecursionError, OverflowError, ImportError, PermissionError, UnicodeDecodeError, ConnectionError, TimeoutError, MemoryError, AssertionError

## 標準ライブラリ (一部)

| カテゴリ | 関数 |
|---|---|
| 型変換 | `to_int`, `to_float`, `to_string`, `to_bool`, `to_list`, `is_int`, `is_string`... |
| コレクション | `length`, `sort`, `reverse`, `unique`, `flatten`, `chunk`, `zip_lists`, `find`, `group_by`... |
| 文字列 | `trim`, `upper`, `lower`, `replace`, `split`, `join`, `regex_match`... |
| 数学 | `PI`, `sqrt`, `floor`, `ceil`, `sin`, `cos`, `clamp`, `lerp`... |
| ファイル | `read_file`, `write_file`, `read_lines`, `file_exists`... |
| JSON | `json_parse`, `json_stringify`, `json_read`, `json_write` |
| HTTP | `http_get`, `http_post` |
| 時間 | `now`, `now_string`, `sleep`, `measure` |
| デバッグ | `debug`, `assert_true`, `assert_equal`, `time_it` |

## 開発ツール

- **VS Code拡張** - `vscode-smile/` にシンタックスハイライト
- **LSPサーバー** - `python -m smile.lsp` で補完・ホバー・診断
- **デバッガー** - `smile debug file.smile` でステップ実行
- **フォーマッター** - `smile fmt file.smile` でコード整形

## 低レイヤー

```
// メモリ操作
mem = memory_new(256, 0x7C00, "BootSector")
mem.write_u8(0, 0xEB)
mem.write_string(3, "SMILE")

// BIOS情報
info = bios_info()
print(to_string(info))

// アセンブラ
code = asm_new(bits=16, base=0x7C00)
code.mov_ah(0x0E)
code.mov_al(0x41)
code.int_(0x10)
code.hlt()
```

## ライセンス

MIT
