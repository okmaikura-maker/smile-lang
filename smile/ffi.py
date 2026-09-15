"""Smile FFI - 他言語との連携

C, C++, Rust, Go, Zig, Fortran, Delphi... どんな言語でも
DLL/SO を作ればSmileから直接呼べる。

使い方:
  lib = ffi_load("mylib.dll")
  lib.call("add", [10, 20], ret="int")

  # 型付き定義
  lib.define("add", ["int", "int"], "int")
  result = lib.add(10, 20)

  # 構造体
  Point = ffi_struct("Point", [("x", "double"), ("y", "double")])
  p = Point(x=1.0, y=2.0)

  # コールバック (Smile関数をC側に渡す)
  cb = ffi_callback(my_func, ["int", "int"], "int")
  lib.call("register_callback", [cb])

  # インラインC (TCC / cl.exe / gcc で即コンパイル)
  lib = ffi_compile('''
  __declspec(dllexport) int add(int a, int b) { return a + b; }
  ''')
  lib.add(1, 2)
"""

import ctypes
import ctypes.util
import sys
import os
import struct
import tempfile
import subprocess

_is_windows = sys.platform == "win32"

# ============================================================
# 型マッピング
# ============================================================

_TYPE_MAP = {
    "void":     None,
    "bool":     ctypes.c_bool,
    "char":     ctypes.c_char,
    "byte":     ctypes.c_ubyte,
    "int8":     ctypes.c_int8,
    "int16":    ctypes.c_int16,
    "int32":    ctypes.c_int32,
    "int":      ctypes.c_int,
    "int64":    ctypes.c_int64,
    "uint8":    ctypes.c_uint8,
    "uint16":   ctypes.c_uint16,
    "uint32":   ctypes.c_uint32,
    "uint":     ctypes.c_uint,
    "uint64":   ctypes.c_uint64,
    "float":    ctypes.c_float,
    "float32":  ctypes.c_float,
    "double":   ctypes.c_double,
    "float64":  ctypes.c_double,
    "string":   ctypes.c_char_p,
    "wstring":  ctypes.c_wchar_p,
    "pointer":  ctypes.c_void_p,
    "ptr":      ctypes.c_void_p,
    "size_t":   ctypes.c_size_t,
}

def _resolve_type(t):
    if t is None or t == "void":
        return None
    if isinstance(t, str):
        if t in _TYPE_MAP:
            return _TYPE_MAP[t]
        if t.endswith("*"):
            return ctypes.c_void_p
        raise ValueError(f"不明な型: '{t}' (使える型: {', '.join(_TYPE_MAP.keys())})")
    return t


# ============================================================
# FFI ライブラリラッパー
# ============================================================

class FFILib:
    """DLL/SO をラップして関数呼び出しを提供"""

    def __init__(self, handle, path):
        self._handle = handle
        self._path = path
        self._defs = {}

    def __repr__(self):
        return f"FFILib({self._path})"

    def define(self, name, arg_types, ret_type="void"):
        """関数のシグネチャを定義"""
        func = getattr(self._handle, name)
        func.argtypes = [_resolve_type(t) for t in arg_types]
        func.restype = _resolve_type(ret_type)
        self._defs[name] = func
        return func

    def call(self, name, args=None, ret="void"):
        """関数を呼び出す (動的)"""
        if args is None:
            args = []
        if name in self._defs:
            return self._defs[name](*args)
        func = getattr(self._handle, name)
        func.restype = _resolve_type(ret)
        return func(*args)

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        if name in self._defs:
            return self._defs[name]
        try:
            func = getattr(self._handle, name)
            return func
        except AttributeError:
            raise AttributeError(f"関数 '{name}' がライブラリに見つかりません: {self._path}")

    def symbols(self):
        """エクスポートされたシンボル一覧 (Windows PE のみ)"""
        if not _is_windows:
            return ["(Linux/macでは nm コマンドで確認してください)"]
        return _list_exports_pe(self._path)

    def close(self):
        """ライブラリをアンロード"""
        if _is_windows:
            ctypes.windll.kernel32.FreeLibrary(ctypes.c_void_p(self._handle._handle))


def _list_exports_pe(path):
    """PEのエクスポートテーブルを読む"""
    try:
        with open(path, "rb") as f:
            data = f.read()
        if data[:2] != b"MZ":
            return []
        pe_off = struct.unpack_from("<I", data, 0x3C)[0]
        if data[pe_off:pe_off+4] != b"PE\0\0":
            return []
        is64 = struct.unpack_from("<H", data, pe_off + 4)[0] == 0x8664
        opt_off = pe_off + 24
        export_rva = struct.unpack_from("<I", data, opt_off + (112 if is64 else 96))[0]
        if export_rva == 0:
            return []
        # セクションからRVA→ファイルオフセット変換
        num_sections = struct.unpack_from("<H", data, pe_off + 6)[0]
        opt_size = struct.unpack_from("<H", data, pe_off + 20)[0]
        sec_off = opt_off + opt_size
        def rva_to_file(rva):
            for i in range(num_sections):
                s = sec_off + i * 40
                vs = struct.unpack_from("<I", data, s + 8)[0]
                va = struct.unpack_from("<I", data, s + 12)[0]
                rs = struct.unpack_from("<I", data, s + 16)[0]
                rp = struct.unpack_from("<I", data, s + 20)[0]
                if va <= rva < va + max(vs, rs):
                    return rp + (rva - va)
            return rva
        eo = rva_to_file(export_rva)
        num_names = struct.unpack_from("<I", data, eo + 24)[0]
        names_rva = struct.unpack_from("<I", data, eo + 32)[0]
        names_off = rva_to_file(names_rva)
        syms = []
        for i in range(num_names):
            name_rva = struct.unpack_from("<I", data, names_off + i * 4)[0]
            name_fo = rva_to_file(name_rva)
            end = data.index(b"\0", name_fo)
            syms.append(data[name_fo:end].decode("ascii", errors="replace"))
        return syms
    except Exception:
        return []


# ============================================================
# FFI 構造体
# ============================================================

def ffi_struct(name, fields):
    """ctypes構造体を作る
    fields: [("name", "type"), ...] or [["name", "type"], ...]
    """
    cfields = []
    for f in fields:
        fname, ftype = f[0], f[1]
        ct = _resolve_type(ftype)
        if ct is None:
            ct = ctypes.c_int
        cfields.append((fname, ct))

    cls = type(name, (ctypes.Structure,), {"_fields_": cfields})
    return cls


# ============================================================
# コールバック
# ============================================================

def ffi_callback(func, arg_types, ret_type="void"):
    """Python/Smile関数をCコールバックに変換"""
    c_arg_types = [_resolve_type(t) for t in arg_types]
    c_ret_type = _resolve_type(ret_type)
    FUNCTYPE = ctypes.CFUNCTYPE(c_ret_type, *c_arg_types)
    cb = FUNCTYPE(func)
    cb._prevent_gc = func
    return cb


# ============================================================
# ライブラリロード
# ============================================================

def ffi_load(path):
    """DLL/SO をロードする

    パス指定: ffi_load("mylib.dll") / ffi_load("./libfoo.so")
    システム: ffi_load("kernel32") / ffi_load("msvcrt")
    """
    # 絶対パスでなければ探す
    if not os.path.isabs(path) and not os.path.exists(path):
        # 拡張子なければ付ける
        if not any(path.endswith(ext) for ext in (".dll", ".so", ".dylib")):
            if _is_windows:
                path_try = path + ".dll"
            elif sys.platform == "darwin":
                path_try = "lib" + path + ".dylib"
            else:
                path_try = "lib" + path + ".so"
            if os.path.exists(path_try):
                path = path_try
            else:
                found = ctypes.util.find_library(path)
                if found:
                    path = found

    try:
        if _is_windows:
            handle = ctypes.CDLL(path, winmode=0)
        else:
            handle = ctypes.CDLL(path)
    except OSError as e:
        raise RuntimeError(f"ライブラリをロードできません: {path}\n  {e}")

    return FFILib(handle, path)


# ============================================================
# インラインCコンパイル
# ============================================================

_temp_dlls = []

def ffi_compile(c_source, name="smile_ffi", extra_flags=None):
    """Cソースを即座にコンパイルしてロード

    コンパイラ検索順: cl.exe → gcc → tcc → clang
    """
    tmp_dir = tempfile.mkdtemp(prefix="smile_ffi_")
    src_path = os.path.join(tmp_dir, f"{name}.c")
    if _is_windows:
        out_path = os.path.join(tmp_dir, f"{name}.dll")
    else:
        out_path = os.path.join(tmp_dir, f"{name}.so")

    with open(src_path, "w", encoding="utf-8") as f:
        f.write(c_source)

    compiler = _find_c_compiler()
    if compiler is None:
        raise RuntimeError(
            "Cコンパイラが見つかりません。\n"
            "以下のいずれかをインストールしてください:\n"
            "  - Visual Studio (cl.exe)\n"
            "  - GCC (gcc / MinGW)\n"
            "  - TCC (tcc)\n"
            "  - Clang (clang)"
        )

    flags = extra_flags or []
    cname, cpath = compiler

    try:
        if cname == "cl":
            cmd = [cpath, "/nologo", "/LD", "/O2", src_path, f"/Fe{out_path}"] + flags
        elif cname in ("gcc", "cc"):
            if _is_windows:
                cmd = [cpath, "-shared", "-O2", "-o", out_path, src_path] + flags
            else:
                cmd = [cpath, "-shared", "-fPIC", "-O2", "-o", out_path, src_path] + flags
        elif cname == "tcc":
            cmd = [cpath, "-shared", "-o", out_path, src_path] + flags
        elif cname == "clang":
            if _is_windows:
                cmd = [cpath, "-shared", "-O2", "-o", out_path, src_path] + flags
            else:
                cmd = [cpath, "-shared", "-fPIC", "-O2", "-o", out_path, src_path] + flags
        else:
            cmd = [cpath, "-shared", "-O2", "-o", out_path, src_path] + flags

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            raise RuntimeError(
                f"コンパイルエラー ({cname}):\n{result.stderr}\n{result.stdout}"
            )
    except FileNotFoundError:
        raise RuntimeError(f"コンパイラ '{cpath}' を実行できません")

    import atexit
    _temp_dlls.append(tmp_dir)
    atexit.register(lambda d=tmp_dir: _cleanup_dir(d))

    return ffi_load(out_path)


def _find_c_compiler():
    """利用可能なCコンパイラを探す"""
    for name in ["cl", "gcc", "tcc", "clang", "cc"]:
        path = _which(name)
        if path:
            return (name, path)
    # Windows: Visual Studio のcl.exeを探す
    if _is_windows:
        for vsdir in [
            r"C:\Program Files\Microsoft Visual Studio",
            r"C:\Program Files (x86)\Microsoft Visual Studio",
        ]:
            if os.path.isdir(vsdir):
                for root, dirs, files in os.walk(vsdir):
                    if "cl.exe" in files:
                        return ("cl", os.path.join(root, "cl.exe"))
    return None


def _which(cmd):
    """コマンドのパスを探す"""
    try:
        if _is_windows:
            result = subprocess.run(
                ["where", cmd], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip().split("\n")[0].strip()
        else:
            result = subprocess.run(
                ["which", cmd], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
    except Exception:
        pass
    return None


def _cleanup_dir(d):
    try:
        import shutil
        shutil.rmtree(d, ignore_errors=True)
    except Exception:
        pass


# ============================================================
# 配列ヘルパー
# ============================================================

def ffi_array(type_name, data):
    """Pythonリストからctypes配列を作る"""
    ct = _resolve_type(type_name)
    arr = (ct * len(data))(*data)
    return arr

def ffi_buffer(size):
    """バイトバッファを確保"""
    return (ctypes.c_ubyte * size)()

def ffi_cast(ptr, type_name):
    """ポインタを別の型にキャスト"""
    ct = _resolve_type(type_name)
    return ctypes.cast(ptr, ctypes.POINTER(ct))

def ffi_sizeof(type_name):
    """型のサイズをバイト数で返す"""
    ct = _resolve_type(type_name)
    if ct is None:
        return 0
    return ctypes.sizeof(ct)

def ffi_null():
    """NULLポインタ"""
    return ctypes.c_void_p(None)

def ffi_string(s, encoding="utf-8"):
    """Python文字列をCの文字列ポインタに変換"""
    return ctypes.c_char_p(s.encode(encoding))

def ffi_from_string(ptr, encoding="utf-8"):
    """Cの文字列ポインタからPython文字列に変換"""
    if isinstance(ptr, bytes):
        return ptr.decode(encoding)
    return ctypes.cast(ptr, ctypes.c_char_p).value.decode(encoding)
