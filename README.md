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
- **低レイヤーアクセス** - BIOS/SMBIOS/ACPI読み取り、メモリ操作、アセンブラも安全に

## インストール

```bash
pip install lark
```

リポジトリをクローンして使う:

```bash
git clone https://github.com/yourname/smile-lang.git
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

## CLIコマンド

```
smile <ファイル.smile>        ファイルを実行
smile run <ファイル.smile>    ファイルを実行 (引数渡し可)
smile init [名前]             新しいプロジェクトを作成
smile test [ディレクトリ]     テストを実行
smile install <パッケージ>    PyPIから一時取得
smile repl                    対話モード
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
