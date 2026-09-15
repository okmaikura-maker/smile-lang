"""Smile 標準ライブラリ - import不要で最初から使える関数群

オーバーヘッドを減らすため、重いモジュールは遅延importする。
Pythonのbuiltinは全てそのまま使える。
"""

import sys as _sys
import os as _os

# ============================================================
# 遅延import用ヘルパー
# ============================================================
def _lazy(name):
    import importlib
    return importlib.import_module(name)

# ============================================================
# 型変換
# ============================================================
def to_int(x):
    return int(x)

def to_float(x):
    return float(x)

def to_string(x):
    return str(x)

def to_bool(x):
    return bool(x)

def to_list(x):
    return list(x)

def to_set(x):
    return set(x)

def to_tuple(x):
    return tuple(x)

def type_of(x):
    return type(x).__name__

def is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)

def is_float(x):
    return isinstance(x, float)

def is_string(x):
    return isinstance(x, str)

def is_list(x):
    return isinstance(x, list)

def is_dict(x):
    return isinstance(x, dict)

def is_bool(x):
    return isinstance(x, bool)

def is_none(x):
    return x is None

# ============================================================
# 入出力
# ============================================================
def input_smile(prompt=""):
    return input(prompt)

def read_file(path, encoding="utf-8"):
    with open(path, "r", encoding=encoding) as f:
        return f.read()

def write_file(path, content, encoding="utf-8"):
    with open(path, "w", encoding=encoding) as f:
        f.write(content)

def append_file(path, content, encoding="utf-8"):
    with open(path, "a", encoding=encoding) as f:
        f.write(content)

def read_lines(path, encoding="utf-8"):
    with open(path, "r", encoding=encoding) as f:
        return [line.rstrip("\n") for line in f]

def write_lines(path, lines, encoding="utf-8"):
    with open(path, "w", encoding=encoding) as f:
        for line in lines:
            f.write(str(line) + "\n")

def file_exists(path):
    return _os.path.exists(path)

def dir_exists(path):
    return _os.path.isdir(path)

def make_dir(path):
    _os.makedirs(path, exist_ok=True)

def list_dir(path="."):
    return _os.listdir(path)

def current_dir():
    return _os.getcwd()

def join_path(*parts):
    return _os.path.join(*parts)

def file_name(path):
    return _os.path.basename(path)

def file_ext(path):
    return _os.path.splitext(path)[1]

def file_size(path):
    return _os.path.getsize(path)

def delete_file(path):
    _os.remove(path)

# ============================================================
# コレクション (リスト・辞書・セット)
# ============================================================
def length(x):
    return len(x)

def range_smile(*args):
    return list(range(*args))

def contains(collection, item):
    return item in collection

def push(lst, item):
    lst.append(item)
    return lst

def pop(lst, index=-1):
    return lst.pop(index)

def insert(lst, index, item):
    lst.insert(index, item)
    return lst

def remove(lst, item):
    lst.remove(item)
    return lst

def index_of(lst, item):
    try:
        return lst.index(item)
    except ValueError:
        return -1

def count(lst, item):
    return lst.count(item)

def reverse(lst):
    return list(reversed(lst))

def sort(lst, key=None, reverse=False):
    return sorted(lst, key=key, reverse=reverse)

def unique(lst):
    seen = set()
    result = []
    for item in lst:
        h = id(item) if isinstance(item, (list, dict, set)) else item
        if h not in seen:
            seen.add(h)
            result.append(item)
    return result

def flatten(lst):
    result = []
    for item in lst:
        if isinstance(item, list):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result

def zip_lists(*lists):
    return [list(t) for t in zip(*lists)]

def enumerate_list(lst, start=0):
    return [[i, v] for i, v in enumerate(lst, start)]

def map_list(fn, lst):
    return list(map(fn, lst))

def filter_list(fn, lst):
    return list(filter(fn, lst))

def reduce_list(fn, lst, initial=None):
    from functools import reduce as _reduce
    if initial is not None:
        return _reduce(fn, lst, initial)
    return _reduce(fn, lst)

def any_of(fn, lst):
    return any(fn(x) for x in lst)

def all_of(fn, lst):
    return all(fn(x) for x in lst)

def find(fn, lst):
    for x in lst:
        if fn(x):
            return x
    return None

def find_index(fn, lst):
    for i, x in enumerate(lst):
        if fn(x):
            return i
    return -1

def group_by(fn, lst):
    result = {}
    for item in lst:
        key = fn(item)
        if key not in result:
            result[key] = []
        result[key].append(item)
    return result

def chunk(lst, size):
    return [lst[i:i+size] for i in range(0, len(lst), size)]

def take(lst, n):
    return lst[:n]

def drop(lst, n):
    return lst[n:]

def slice_list(lst, start=None, end=None, step=None):
    return lst[start:end:step]

# 辞書
def keys(d):
    return list(d.keys())

def values(d):
    return list(d.values())

def items(d):
    return [[k, v] for k, v in d.items()]

def merge(*dicts):
    result = {}
    for d in dicts:
        result.update(d)
    return result

def pick(d, ks):
    return {k: d[k] for k in ks if k in d}

def omit(d, ks):
    ks_set = set(ks)
    return {k: v for k, v in d.items() if k not in ks_set}

def get(d, key, default=None):
    return d.get(key, default)

# ============================================================
# 文字列
# ============================================================
def split(s, sep=None):
    return s.split(sep)

def join(lst, sep=""):
    return sep.join(str(x) for x in lst)

def trim(s):
    return s.strip()

def trim_left(s):
    return s.lstrip()

def trim_right(s):
    return s.rstrip()

def upper(s):
    return s.upper()

def lower(s):
    return s.lower()

def title(s):
    return s.title()

def replace(s, old, new, count=-1):
    return s.replace(old, new) if count < 0 else s.replace(old, new, count)

def starts_with(s, prefix):
    return s.startswith(prefix)

def ends_with(s, suffix):
    return s.endswith(suffix)

def pad_left(s, width, char=" "):
    return s.rjust(width, char)

def pad_right(s, width, char=" "):
    return s.ljust(width, char)

def repeat(s, n):
    return s * n

def char_at(s, index):
    return s[index]

def substring(s, start, end=None):
    return s[start:end]

def format_string(template, *args, **kwargs):
    return template.format(*args, **kwargs)

def regex_match(pattern, s):
    import re
    m = re.search(pattern, s)
    return m.group(0) if m else None

def regex_find_all(pattern, s):
    import re
    return re.findall(pattern, s)

def regex_replace(pattern, replacement, s):
    import re
    return re.sub(pattern, replacement, s)

def regex_split(pattern, s):
    import re
    return re.split(pattern, s)

# ============================================================
# 数学
# ============================================================
def abs_val(x):
    return abs(x)

def max_val(*args):
    if len(args) == 1 and hasattr(args[0], "__iter__"):
        return max(args[0])
    return max(args)

def min_val(*args):
    if len(args) == 1 and hasattr(args[0], "__iter__"):
        return min(args[0])
    return min(args)

def sum_val(lst):
    return sum(lst)

def round_val(x, digits=0):
    return round(x, digits)

def floor(x):
    import math
    return math.floor(x)

def ceil(x):
    import math
    return math.ceil(x)

def power(base, exp):
    return base ** exp

def sqrt(x):
    import math
    return math.sqrt(x)

def log(x, base=None):
    import math
    return math.log(x) if base is None else math.log(x, base)

def sin(x):
    import math
    return math.sin(x)

def cos(x):
    import math
    return math.cos(x)

def tan(x):
    import math
    return math.tan(x)

PI = 3.141592653589793
E = 2.718281828459045
INF = float("inf")

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def lerp(a, b, t):
    return a + (b - a) * t

def is_even(n):
    return n % 2 == 0

def is_odd(n):
    return n % 2 != 0

# ============================================================
# ランダム
# ============================================================
def random_int(a, b):
    import random
    return random.randint(a, b)

def random_float(a=0.0, b=1.0):
    import random
    return random.uniform(a, b)

def random_choice(lst):
    import random
    return random.choice(lst)

def random_shuffle(lst):
    import random
    result = lst[:]
    random.shuffle(result)
    return result

def random_sample(lst, n):
    import random
    return random.sample(lst, n)

# ============================================================
# 時間
# ============================================================
def now():
    import time
    return time.time()

def now_string(fmt="%Y-%m-%d %H:%M:%S"):
    from datetime import datetime
    return datetime.now().strftime(fmt)

def sleep(seconds):
    import time
    time.sleep(seconds)

def measure(fn):
    import time
    start = time.perf_counter()
    result = fn()
    elapsed = time.perf_counter() - start
    return {"result": result, "time": elapsed}

# ============================================================
# JSON
# ============================================================
def json_parse(s):
    import json
    return json.loads(s)

def json_stringify(obj, pretty=True):
    import json
    if pretty:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    return json.dumps(obj, ensure_ascii=False)

def json_read(path):
    import json
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def json_write(path, obj, pretty=True):
    import json
    with open(path, "w", encoding="utf-8") as f:
        if pretty:
            json.dump(obj, f, ensure_ascii=False, indent=2)
        else:
            json.dump(obj, f, ensure_ascii=False)

# ============================================================
# CSV
# ============================================================
def csv_read(path, has_header=True):
    import csv
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)
    if has_header and rows:
        header = rows[0]
        return [dict(zip(header, row)) for row in rows[1:]]
    return rows

def csv_write(path, data, header=None):
    import csv
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        if header:
            writer.writerow(header)
        if data and isinstance(data[0], dict):
            if not header:
                header = list(data[0].keys())
                writer.writerow(header)
            for row in data:
                writer.writerow([row.get(k, "") for k in header])
        else:
            writer.writerows(data)

# ============================================================
# HTTP (requests風の薄いラッパー)
# ============================================================
def http_get(url, headers=None):
    from urllib.request import Request, urlopen
    req = Request(url, headers=headers or {})
    with urlopen(req) as resp:
        body = resp.read().decode("utf-8")
        return {"status": resp.status, "body": body, "headers": dict(resp.headers)}

def http_post(url, data=None, json_data=None, headers=None):
    from urllib.request import Request, urlopen
    import json
    h = headers or {}
    if json_data is not None:
        body = json.dumps(json_data).encode("utf-8")
        h["Content-Type"] = "application/json"
    elif data is not None:
        body = data.encode("utf-8") if isinstance(data, str) else data
    else:
        body = None
    req = Request(url, data=body, headers=h, method="POST")
    with urlopen(req) as resp:
        rbody = resp.read().decode("utf-8")
        return {"status": resp.status, "body": rbody, "headers": dict(resp.headers)}

# ============================================================
# ハッシュ・エンコーディング
# ============================================================
def hash_md5(s):
    import hashlib
    return hashlib.md5(s.encode("utf-8")).hexdigest()

def hash_sha256(s):
    import hashlib
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def base64_encode(s):
    import base64
    return base64.b64encode(s.encode("utf-8")).decode("ascii")

def base64_decode(s):
    import base64
    return base64.b64decode(s.encode("ascii")).decode("utf-8")

def url_encode(s):
    from urllib.parse import quote
    return quote(s)

def url_decode(s):
    from urllib.parse import unquote
    return unquote(s)

# ============================================================
# プロセス・システム
# ============================================================
def run_command(cmd):
    import subprocess
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return {"code": result.returncode, "stdout": result.stdout, "stderr": result.stderr}

def env(name, default=None):
    return _os.environ.get(name, default)

def args():
    return _sys.argv[1:]

def exit_program(code=0):
    _sys.exit(code)

def platform():
    return _sys.platform

# ============================================================
# デバッグ・ユーティリティ
# ============================================================
def debug(*values):
    import inspect
    frame = inspect.currentframe().f_back
    info = inspect.getframeinfo(frame)
    parts = []
    for v in values:
        parts.append(f"{type(v).__name__}: {v!r}")
    loc = f"{_os.path.basename(info.filename)}:{info.lineno}"
    print(f"[DEBUG {loc}] {', '.join(parts)}")

def assert_true(condition, message=""):
    if not condition:
        raise AssertionError(message or "アサーション失敗: 条件がfalseです")

def assert_equal(a, b, message=""):
    if a != b:
        raise AssertionError(message or f"アサーション失敗: {a!r} != {b!r}")

def time_it(label, fn):
    import time
    start = time.perf_counter()
    result = fn()
    elapsed = time.perf_counter() - start
    print(f"[{label}] {elapsed:.4f} 秒")
    return result

def typeof(x):
    return type(x).__name__

# ============================================================
# 低レイヤーライブラリ (遅延import)
# ============================================================
from smile.lowlevel import *

# ============================================================
# 全エクスポート
# ============================================================
def _get_all_exports():
    import types
    g = globals()
    return {name: obj for name, obj in g.items()
            if not name.startswith("_")
            and (callable(obj) or not isinstance(obj, types.ModuleType))}

EXPORTS = _get_all_exports()
