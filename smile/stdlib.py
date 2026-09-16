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
# UUID
# ============================================================
def uuid4():
    import uuid
    return str(uuid.uuid4())

def uuid_short():
    import uuid
    return uuid.uuid4().hex[:8]

# ============================================================
# 圧縮・展開
# ============================================================
def compress(data, level=9):
    import zlib
    if isinstance(data, str):
        data = data.encode("utf-8")
    return zlib.compress(data, level)

def decompress(data):
    import zlib
    return zlib.decompress(data)

def gzip_compress(data):
    import gzip
    if isinstance(data, str):
        data = data.encode("utf-8")
    return gzip.compress(data)

def gzip_decompress(data):
    import gzip
    return gzip.decompress(data)

# ============================================================
# SQLite (import不要データベース)
# ============================================================
def db_open(path=":memory:"):
    import sqlite3
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn

def db_exec(conn, sql, params=None):
    cur = conn.execute(sql, params or [])
    conn.commit()
    return cur

def db_query(conn, sql, params=None):
    cur = conn.execute(sql, params or [])
    return [dict(row) for row in cur.fetchall()]

def db_close(conn):
    conn.close()

# ============================================================
# 暗号・セキュリティ
# ============================================================
def hmac_sha256(key, msg):
    import hmac, hashlib
    if isinstance(key, str):
        key = key.encode("utf-8")
    if isinstance(msg, str):
        msg = msg.encode("utf-8")
    return hmac.new(key, msg, hashlib.sha256).hexdigest()

def random_bytes(n):
    import secrets
    return secrets.token_bytes(n)

def random_hex(n):
    import secrets
    return secrets.token_hex(n)

def random_token(n=32):
    import secrets
    return secrets.token_urlsafe(n)

# ============================================================
# 並列・非同期
# ============================================================
def parallel_for(func, items, workers=None):
    import concurrent.futures, os
    w = workers or (os.cpu_count() or 4)
    items_list = list(items)
    try:
        with concurrent.futures.ProcessPoolExecutor(max_workers=w) as ex:
            return list(ex.map(func, items_list, chunksize=max(1, len(items_list) // w)))
    except Exception:
        with concurrent.futures.ThreadPoolExecutor(max_workers=w) as ex:
            return list(ex.map(func, items_list))

def thread_map(func, items, workers=None):
    import concurrent.futures, os
    w = workers or (os.cpu_count() or 4)
    with concurrent.futures.ThreadPoolExecutor(max_workers=w) as ex:
        return list(ex.map(func, list(items)))

def async_run(coro):
    import asyncio
    return asyncio.run(coro)

def async_gather(*coros):
    import asyncio
    async def _g():
        return await asyncio.gather(*coros)
    return asyncio.run(_g())

# ============================================================
# デコレータ
# ============================================================
def cache(func):
    from functools import lru_cache
    return lru_cache(maxsize=None)(func)

def retry(n=3, delay=0.1):
    import time, functools
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*a, **kw):
            for i in range(n):
                try:
                    return func(*a, **kw)
                except Exception:
                    if i == n - 1:
                        raise
                    time.sleep(delay)
        return wrapper
    return decorator

def throttle(seconds):
    import time, functools
    def decorator(func):
        last = [0.0]
        @functools.wraps(func)
        def wrapper(*a, **kw):
            now = time.time()
            if now - last[0] >= seconds:
                last[0] = now
                return func(*a, **kw)
        return wrapper
    return decorator

def once(func):
    import functools
    result = []
    @functools.wraps(func)
    def wrapper(*a, **kw):
        if not result:
            result.append(func(*a, **kw))
        return result[0]
    return wrapper

# ============================================================
# 関数型プログラミング
# ============================================================
def compose(*fns):
    def composed(x):
        for f in reversed(fns):
            x = f(x)
        return x
    return composed

def pipe_fn(*fns):
    def piped(x):
        for f in fns:
            x = f(x)
        return x
    return piped

def partial(func, *args, **kwargs):
    from functools import partial as _partial
    return _partial(func, *args, **kwargs)

def identity(x):
    return x

def constantly(x):
    return lambda *a, **kw: x

def juxt(*fns):
    def juxtaposed(*a, **kw):
        return [f(*a, **kw) for f in fns]
    return juxtaposed

# ============================================================
# テンプレート・フォーマッタ
# ============================================================
def table(headers, rows, padding=2):
    widths = [len(str(h)) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))
    sep = " " * padding
    header_line = sep.join(str(h).ljust(widths[i]) for i, h in enumerate(headers))
    divider = sep.join("-" * w for w in widths)
    lines = [header_line, divider]
    for row in rows:
        lines.append(sep.join(str(cell).ljust(widths[i]) for i, cell in enumerate(row)))
    return "\n".join(lines)

def progress_bar(current, total, width=40, label=""):
    filled = int(width * current / total) if total > 0 else 0
    bar = "█" * filled + "░" * (width - filled)
    pct = 100 * current / total if total > 0 else 0
    return f"{label}|{bar}| {pct:.1f}% ({current}/{total})"

def color(text, code):
    codes = {"red": 31, "green": 32, "yellow": 33, "blue": 34,
             "magenta": 35, "cyan": 36, "white": 37, "bold": 1, "dim": 2}
    c = codes.get(code, code) if isinstance(code, str) else code
    return f"\033[{c}m{text}\033[0m"

# ============================================================
# バリデーション
# ============================================================
def is_email(s):
    import re
    return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', s))

def is_url(s):
    import re
    return bool(re.match(r'^https?://[^\s]+$', s))

def is_ip(s):
    parts = s.split(".")
    if len(parts) != 4:
        return False
    return all(p.isdigit() and 0 <= int(p) <= 255 for p in parts)

def is_json(s):
    import json
    try:
        json.loads(s)
        return True
    except Exception:
        return False

def is_number(s):
    try:
        float(s)
        return True
    except (ValueError, TypeError):
        return False

# ============================================================
# データ変換
# ============================================================
def to_bytes(s, encoding="utf-8"):
    if isinstance(s, bytes):
        return s
    return s.encode(encoding)

def from_bytes(b, encoding="utf-8"):
    if isinstance(b, str):
        return b
    return b.decode(encoding)

def hex_encode(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    return data.hex()

def hex_decode(s):
    return bytes.fromhex(s)

# ============================================================
# 統計
# ============================================================
def mean(lst):
    return sum(lst) / len(lst)

def median(lst):
    s = sorted(lst)
    n = len(s)
    if n % 2 == 1:
        return s[n // 2]
    return (s[n // 2 - 1] + s[n // 2]) / 2

def stdev(lst):
    m = mean(lst)
    variance = sum((x - m) ** 2 for x in lst) / len(lst)
    return variance ** 0.5

def percentile(lst, p):
    s = sorted(lst)
    k = (len(s) - 1) * (p / 100.0)
    f = int(k)
    c = f + 1
    if c >= len(s):
        return s[f]
    return s[f] + (k - f) * (s[c] - s[f])

def histogram(lst, bins=10):
    lo, hi = min(lst), max(lst)
    width = (hi - lo) / bins if hi != lo else 1
    counts = [0] * bins
    for x in lst:
        idx = min(int((x - lo) / width), bins - 1)
        counts[idx] += 1
    return [{"low": lo + i * width, "high": lo + (i + 1) * width, "count": c}
            for i, c in enumerate(counts)]

# ============================================================
# ネットワーク
# ============================================================
def download(url, path):
    from urllib.request import urlretrieve
    urlretrieve(url, path)
    return path

def ip_address():
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        addr = s.getsockname()[0]
        s.close()
        return addr
    except Exception:
        return "127.0.0.1"

def hostname():
    import socket
    return socket.gethostname()

def port_open(host, port, timeout=1.0):
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, port))
        s.close()
        return True
    except Exception:
        return False

# ============================================================
# 日時
# ============================================================
def today():
    from datetime import date
    return str(date.today())

def timestamp():
    import time
    return int(time.time())

def datetime_parse(s, fmt="%Y-%m-%d %H:%M:%S"):
    from datetime import datetime
    return datetime.strptime(s, fmt)

def datetime_format(dt, fmt="%Y-%m-%d %H:%M:%S"):
    return dt.strftime(fmt)

def time_diff(start, end):
    return end - start

def stopwatch():
    import time
    t0 = time.perf_counter()
    class SW:
        def elapsed(self):
            return time.perf_counter() - t0
        def lap(self):
            return time.perf_counter() - t0
        def __repr__(self):
            return f"Stopwatch({self.elapsed():.4f}s)"
    return SW()

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
# FFI - 他言語連携 (標準関数)
# ============================================================
from smile.ffi import (
    ffi_load, ffi_compile, ffi_struct, ffi_callback,
    ffi_array, ffi_buffer, ffi_cast, ffi_sizeof, ffi_null,
    ffi_string, ffi_from_string,
)

# ============================================================
# Compute - GPU/iGPU/CPU 計算エンジン (標準関数)
# ============================================================
from smile.compute import (
    compute, gpu_exec, gpu_compute, cpu_parallel, parallel_map,
    numpy_gpu, pandas_gpu, pil_gpu, saturate_all, ComputeArray,
)

# ============================================================
# GPU / iGPU / CPU 飽和ベンチマーク (標準関数)
# ============================================================

def bench_gpu(seconds=10.0):
    """NVIDIA GPU を8本独立FMAで完全飽和。GFLOPS を返す"""
    from smile.gpu import gpu_devices, OpenCLGPU
    devs = [d for d in gpu_devices() if d["backend"] == "opencl" and "NVIDIA" in d.get("vendor", "").upper()]
    if not devs:
        print("NVIDIA GPUが見つかりません")
        return None
    return _run_alu_saturate(OpenCLGPU(devs[0]["index"]), devs[0]["name"], seconds)

def bench_igpu(seconds=10.0):
    """Intel/AMD iGPU を8本独立FMAで完全飽和。GFLOPS を返す"""
    from smile.gpu import gpu_devices, OpenCLGPU
    devs = [d for d in gpu_devices() if d["backend"] == "opencl"
            and ("INTEL" in d.get("vendor", "").upper() or "AMD" in d.get("vendor", "").upper())
            and "NVIDIA" not in d.get("vendor", "").upper()]
    if not devs:
        print("iGPUが見つかりません")
        return None
    return _run_alu_saturate(OpenCLGPU(devs[0]["index"]), devs[0]["name"], seconds)

def bench_cpu(seconds=10.0):
    """CPU全コアをネイティブ演算で飽和。GFLOPS を返す"""
    import os, time, threading
    cores = os.cpu_count() or 4

    try:
        import numpy as np
        has_numpy = True
    except ImportError:
        has_numpy = False

    results = [0.0] * cores

    if has_numpy:
        print(f"CPU飽和中... ({cores}コア, {seconds}秒, numpy SIMD)")
        def _work(idx, dur):
            size = 8 * 1024 * 1024
            a = np.full(size, 1.0001, dtype=np.float32)
            b = np.full(size, 0.9999, dtype=np.float32)
            c = np.full(size, 0.0001, dtype=np.float32)
            count = 0
            t0 = time.perf_counter()
            while time.perf_counter() - t0 < dur:
                np.multiply(a, b, out=a)
                np.add(a, c, out=a)
                np.multiply(a, b, out=a)
                np.add(a, c, out=a)
                np.multiply(a, b, out=a)
                np.add(a, c, out=a)
                np.multiply(a, b, out=a)
                np.add(a, c, out=a)
                count += size * 8
            results[idx] = count
        method = "numpy SIMD"
    else:
        print(f"CPU飽和中... ({cores}コア, {seconds}秒, OpenCL CPU)")
        try:
            from smile.gpu import gpu_devices, OpenCLGPU
            cpu_devs = [d for d in gpu_devices() if "cpu" in d.get("type", "").lower()]
            if cpu_devs:
                def _work(idx, dur):
                    gpu = OpenCLGPU(cpu_devs[0]["index"])
                    ksrc = """
__kernel void fma8(__global float* out, const int iters) {
    int i = get_global_id(0);
    float a0=i*1e-6f, a1=a0+.1f, a2=a0+.2f, a3=a0+.3f;
    float a4=a0+.4f, a5=a0+.5f, a6=a0+.6f, a7=a0+.7f;
    for(int k=0;k<iters;k++){
        a0=a0*.9f+.1f; a1=a1*.9f+.1f; a2=a2*.9f+.1f; a3=a3*.9f+.1f;
        a4=a4*.9f+.1f; a5=a5*.9f+.1f; a6=a6*.9f+.1f; a7=a7*.9f+.1f;
    }
    out[i]=a0+a1+a2+a3+a4+a5+a6+a7;
}"""
                    gpu.build(ksrc)
                    kern = gpu.kernel("fma8")
                    gsize = 1024 * 1024
                    iters = 2000
                    buf = gpu.alloc(gsize * 4)
                    count = 0
                    t0 = time.perf_counter()
                    while time.perf_counter() - t0 < dur:
                        kern.launch(gsize, [buf, iters], sync=True)
                        count += gsize * iters * 16
                    results[idx] = count
                method = "OpenCL CPU"
            else:
                raise RuntimeError("no CPU device")
        except Exception:
            def _work(idx, dur):
                a, b = 1.0000001, 0.9999999
                count = 0
                batch = 2_000_000
                t0 = time.perf_counter()
                while time.perf_counter() - t0 < dur:
                    x = a
                    for _ in range(batch):
                        x = x * b + a
                    count += batch * 2
                results[idx] = count
            method = "Python loop"

    threads = []
    t0 = time.perf_counter()
    for i in range(cores):
        t = threading.Thread(target=_work, args=(i, seconds))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    dt = time.perf_counter() - t0

    total_flops = sum(results)
    gflops = total_flops / dt / 1e9
    print(f"CPU: {gflops:.1f} GFLOPS ({cores}コア, {dt:.2f}秒, {method})")
    return {"gflops": gflops, "cores": cores, "seconds": dt, "method": method}

def bench_all(seconds=10.0):
    """GPU + iGPU + CPU を全部飽和させて結果を返す"""
    results = {}
    print("============================================================")
    print("  全デバイス飽和ベンチマーク")
    print("============================================================")
    r = bench_gpu(seconds)
    if r:
        results["gpu"] = r
    r = bench_igpu(seconds)
    if r:
        results["igpu"] = r
    r = bench_cpu(seconds)
    if r:
        results["cpu"] = r
    print("============================================================")
    print("  完了")
    print("============================================================")
    return results

def _run_alu_saturate(gpu, name, seconds):
    """OpenCL GPUで8本独立FMA飽和"""
    import time
    kernel_src = """
__kernel void saturate(__global float* out, const int iters) {
    int i = get_global_id(0);
    float a0 = i * 1e-6f,       a1 = a0 + 0.1f;
    float a2 = a0 + 0.2f,       a3 = a0 + 0.3f;
    float a4 = a0 + 0.4f,       a5 = a0 + 0.5f;
    float a6 = a0 + 0.6f,       a7 = a0 + 0.7f;
    for (int k = 0; k < iters; k++) {
        a0 = a0 * 0.9f + 0.1f;  a1 = a1 * 0.9f + 0.1f;
        a2 = a2 * 0.9f + 0.1f;  a3 = a3 * 0.9f + 0.1f;
        a4 = a4 * 0.9f + 0.1f;  a5 = a5 * 0.9f + 0.1f;
        a6 = a6 * 0.9f + 0.1f;  a7 = a7 * 0.9f + 0.1f;
    }
    out[i] = a0+a1+a2+a3+a4+a5+a6+a7;
}
"""
    gpu.build(kernel_src)
    kern = gpu.kernel("saturate")
    gsize = 1024 * 1024
    iters = 5000
    buf = gpu.alloc(gsize * 4)
    launches = 0
    print(f"{name} 飽和中... ({seconds}秒)")
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < seconds:
        kern.launch(gsize, [buf, iters], sync=False)
        kern.launch(gsize, [buf, iters], sync=False)
        kern.launch(gsize, [buf, iters], sync=False)
        launches += 3
        gpu.sync()
    dt = time.perf_counter() - t0
    flop = launches * gsize * iters * 16
    gflops = flop / dt / 1e9
    print(f"{name}: {gflops:.1f} GFLOPS ({launches} launches, {dt:.2f}秒)")
    return {"name": name, "gflops": gflops, "launches": launches, "seconds": dt}

# ============================================================
# GUI - Win32 GDI直叩きキャンバス (遅延import)
# ============================================================
def window(title="Smile", width=800, height=600):
    from smile.gui import Window
    return Window(title, width, height)

def gui_run(title, width, height, draw_fn, fps=60):
    from smile.gui import gui_run as _gui_run
    return _gui_run(title, width, height, draw_fn, fps)

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
