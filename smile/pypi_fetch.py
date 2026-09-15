"""Smile PyPI 一時取得 - importした瞬間にPyPIからwheelを取得、実行後に自動削除

pipなしで動く。wheelをダウンロード→一時ディレクトリに展開→sys.pathに追加→実行完了後に消す。
"""

import sys
import os
import json
import zipfile
import tempfile
import shutil
import atexit
import importlib
import importlib.abc
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError

# 今回の実行で取得したパッケージ (実行後に消す)
_session_dirs = []


def _normalize(name):
    return name.replace("-", "-").replace("_", "-").lower()


def _pypi_info(package_name):
    url = f"https://pypi.org/pypi/{_normalize(package_name)}/json"
    try:
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (HTTPError, Exception):
        return None


def _pick_wheel(info):
    if not info:
        return None
    urls = info.get("urls", [])
    py_ver = f"cp{sys.version_info.major}{sys.version_info.minor}"
    platform = "win_amd64" if sys.platform == "win32" else "manylinux" if sys.platform == "linux" else "macosx"

    best_platform = None
    best_pure = None
    for u in urls:
        if u["packagetype"] != "bdist_wheel":
            continue
        fn = u["filename"]
        if "none-any" in fn:
            best_pure = u
        elif platform in fn and py_ver in fn:
            best_platform = u

    return best_platform or best_pure


def _download_to_temp(wheel_url, package_name):
    """wheelを一時ディレクトリにダウンロード・展開"""
    tmp_dir = Path(tempfile.mkdtemp(prefix=f"smile_{_normalize(package_name)}_"))

    url = wheel_url["url"]
    try:
        with urlopen(url, timeout=60) as resp:
            data = resp.read()
    except Exception:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return None

    whl_path = tmp_dir / "package.whl"
    whl_path.write_bytes(data)

    try:
        with zipfile.ZipFile(whl_path) as zf:
            zf.extractall(tmp_dir)
    except zipfile.BadZipFile:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return None

    whl_path.unlink()
    _session_dirs.append(tmp_dir)
    return tmp_dir


def fetch_package(package_name):
    """パッケージを一時取得してsys.pathに追加"""
    info = _pypi_info(package_name)
    if not info:
        return False

    wheel = _pick_wheel(info)
    if not wheel:
        return False

    result = _download_to_temp(wheel, package_name)
    if not result:
        return False

    pkg_str = str(result)
    if pkg_str not in sys.path:
        sys.path.insert(0, pkg_str)
    return True


def cleanup():
    """セッション中に取得した一時パッケージを全削除"""
    for d in _session_dirs:
        try:
            shutil.rmtree(d, ignore_errors=True)
        except Exception:
            pass
    _session_dirs.clear()


# プロセス終了時に自動クリーンアップ
atexit.register(cleanup)


IMPORT_TO_PYPI = {
    "cv2": "opencv-python",
    "PIL": "Pillow",
    "sklearn": "scikit-learn",
    "yaml": "PyYAML",
    "bs4": "beautifulsoup4",
    "attr": "attrs",
    "dotenv": "python-dotenv",
    "gi": "PyGObject",
    "serial": "pyserial",
    "usb": "pyusb",
    "wx": "wxPython",
    "Crypto": "pycryptodome",
    "jose": "python-jose",
    "magic": "python-magic",
    "dateutil": "python-dateutil",
}


class PyPIAutoFinder(importlib.abc.MetaPathFinder):
    """importに失敗したとき、PyPIから一時取得を試みるfinder"""

    def __init__(self):
        self._trying = set()

    def find_module(self, fullname, path=None):
        top = fullname.split(".")[0]
        if top in self._trying:
            return None
        if top.startswith("_"):
            return None
        if hasattr(sys, "stdlib_module_names") and top in sys.stdlib_module_names:
            return None
        if top == "smile":
            return None

        pypi_name = IMPORT_TO_PYPI.get(top, top)
        self._trying.add(top)
        try:
            ok = fetch_package(pypi_name)
            if ok:
                return _ReloadHelper(top)
        finally:
            self._trying.discard(top)
        return None


class _ReloadHelper(importlib.abc.Loader):
    def __init__(self, name):
        self.name = name

    def load_module(self, fullname):
        if fullname in sys.modules:
            return sys.modules[fullname]
        finders = [f for f in sys.meta_path if isinstance(f, PyPIAutoFinder)]
        for f in finders:
            sys.meta_path.remove(f)
        try:
            mod = importlib.import_module(fullname)
        finally:
            for f in finders:
                sys.meta_path.append(f)
        return mod


def install():
    """PyPI自動取得finderをsys.meta_pathに登録"""
    for finder in sys.meta_path:
        if isinstance(finder, PyPIAutoFinder):
            return
    sys.meta_path.append(PyPIAutoFinder())
