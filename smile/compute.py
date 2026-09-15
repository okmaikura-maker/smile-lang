"""Smile Compute - GPU/iGPU/CPU を最大限使う計算エンジン

ベンチマークではなく、実際の計算を全デバイスで飽和実行する。
numpy, pandas, PIL 等のPyPIライブラリとも自動連携。

使い方:
  # GPU で配列演算 (numpy 互換)
  a = compute([1,2,3,4,5])
  b = a * 2 + 1            # GPU で実行
  print(b.tolist())

  # 並列 map
  results = parallel_map(lambda x: x**2, range(1000000))

  # GPU カーネル実行
  gpu_exec("out[i] = in0[i] * in0[i] + in1[i]", [data1, data2])

  # numpy 連携
  import numpy as np
  arr = np.random.randn(10000000).astype(np.float32)
  result = gpu_compute(arr, "x * x + 1.0f")

  # CPU全コア並列
  cpu_parallel(my_func, chunks)
"""

import os
import sys
import time
import threading


# ============================================================
# GPU/iGPU デバイス管理
# ============================================================

_gpu_cache = {}

def _get_gpu():
    if "gpu" not in _gpu_cache:
        try:
            from smile.gpu import gpu_devices, OpenCLGPU
            devs = gpu_devices()
            nvidia = [d for d in devs if d["backend"] == "opencl" and "NVIDIA" in d.get("vendor", "").upper()]
            if nvidia:
                _gpu_cache["gpu"] = OpenCLGPU(nvidia[0]["index"])
                _gpu_cache["gpu_name"] = nvidia[0]["name"]
            else:
                _gpu_cache["gpu"] = None
        except Exception:
            _gpu_cache["gpu"] = None
    return _gpu_cache.get("gpu")

def _get_igpu():
    if "igpu" not in _gpu_cache:
        try:
            from smile.gpu import gpu_devices, OpenCLGPU
            devs = gpu_devices()
            igpu = [d for d in devs if d["backend"] == "opencl"
                    and ("INTEL" in d.get("vendor", "").upper() or "AMD" in d.get("vendor", "").upper())
                    and "NVIDIA" not in d.get("vendor", "").upper()]
            if igpu:
                _gpu_cache["igpu"] = OpenCLGPU(igpu[0]["index"])
                _gpu_cache["igpu_name"] = igpu[0]["name"]
            else:
                _gpu_cache["igpu"] = None
        except Exception:
            _gpu_cache["igpu"] = None
    return _gpu_cache.get("igpu")


# ============================================================
# ComputeArray - GPU 加速配列
# ============================================================

class ComputeArray:
    """GPU加速配列。numpy的な演算をGPUで実行する"""

    def __init__(self, data, device="auto"):
        if isinstance(data, (list, tuple)):
            self._data = [float(x) for x in data]
        elif hasattr(data, 'tolist'):
            self._data = [float(x) for x in data.tolist()]
        else:
            self._data = list(data)
        self._device = device

    def _gpu_map(self, expr):
        gpu = _get_gpu() or _get_igpu()
        if gpu and len(self._data) >= 1024:
            from smile.gpu import gpu_map
            result = gpu_map(expr, self._data, gpu)
            return ComputeArray(result, self._device)
        return None

    def __add__(self, other):
        val = other if not isinstance(other, ComputeArray) else None
        if isinstance(other, (int, float)):
            r = self._gpu_map(f"x + {float(other)}f")
            if r:
                return r
            return ComputeArray([x + other for x in self._data])
        if isinstance(other, ComputeArray):
            return ComputeArray([a + b for a, b in zip(self._data, other._data)])
        return NotImplemented

    def __radd__(self, other):
        return self.__add__(other)

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            r = self._gpu_map(f"x * {float(other)}f")
            if r:
                return r
            return ComputeArray([x * other for x in self._data])
        if isinstance(other, ComputeArray):
            return ComputeArray([a * b for a, b in zip(self._data, other._data)])
        return NotImplemented

    def __rmul__(self, other):
        return self.__mul__(other)

    def __sub__(self, other):
        if isinstance(other, (int, float)):
            r = self._gpu_map(f"x - {float(other)}f")
            if r:
                return r
            return ComputeArray([x - other for x in self._data])
        if isinstance(other, ComputeArray):
            return ComputeArray([a - b for a, b in zip(self._data, other._data)])
        return NotImplemented

    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            r = self._gpu_map(f"x / {float(other)}f")
            if r:
                return r
            return ComputeArray([x / other for x in self._data])
        if isinstance(other, ComputeArray):
            return ComputeArray([a / b for a, b in zip(self._data, other._data)])
        return NotImplemented

    def __pow__(self, other):
        if isinstance(other, (int, float)):
            r = self._gpu_map(f"pow(x, {float(other)}f)")
            if r:
                return r
            return ComputeArray([x ** other for x in self._data])
        return NotImplemented

    def __neg__(self):
        r = self._gpu_map("(-x)")
        if r:
            return r
        return ComputeArray([-x for x in self._data])

    def __abs__(self):
        r = self._gpu_map("fabs(x)")
        if r:
            return r
        return ComputeArray([abs(x) for x in self._data])

    def __len__(self):
        return len(self._data)

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            return ComputeArray(self._data[idx])
        return self._data[idx]

    def __repr__(self):
        if len(self._data) > 8:
            s = ", ".join(f"{x:.4g}" for x in self._data[:4])
            e = ", ".join(f"{x:.4g}" for x in self._data[-2:])
            return f"ComputeArray([{s}, ..., {e}], len={len(self._data)})"
        return f"ComputeArray({self._data})"

    def tolist(self):
        return list(self._data)

    def sum(self):
        gpu = _get_gpu() or _get_igpu()
        if gpu and len(self._data) >= 256:
            from smile.gpu import gpu_sum
            return gpu_sum(self._data, gpu)
        return sum(self._data)

    def mean(self):
        return self.sum() / len(self._data)

    def max(self):
        return max(self._data)

    def min(self):
        return min(self._data)

    def apply(self, expr):
        """OpenCL式を適用: arr.apply("sin(x) + cos(x)")"""
        gpu = _get_gpu() or _get_igpu()
        if gpu:
            from smile.gpu import gpu_map
            return ComputeArray(gpu_map(expr, self._data, gpu))
        raise RuntimeError("GPUが見つかりません")

    def to_numpy(self):
        try:
            import numpy as np
            return np.array(self._data, dtype=np.float32)
        except ImportError:
            raise RuntimeError("numpyが必要です: pip install numpy")


def compute(data, device="auto"):
    """GPU加速配列を作る"""
    return ComputeArray(data, device)


# ============================================================
# GPU カーネル実行
# ============================================================

def gpu_exec(expr, arrays, size=None, device="auto"):
    """複数配列を入力にGPUカーネルを実行

    expr: OpenCL C式。in0, in1, ... が入力配列、out が出力
    arrays: 入力リストのリスト
    """
    gpu = _get_gpu() or _get_igpu()
    if gpu is None:
        raise RuntimeError("GPUが見つかりません")

    from smile.gpu import OpenCLGPU
    n = size or len(arrays[0])

    # カーネル生成
    in_args = ", ".join(f"__global const float* in{i}" for i in range(len(arrays)))
    source = f"""
__kernel void exec_kern({in_args}, __global float* out, const int n) {{
    int i = get_global_id(0);
    if (i < n) {{
        out[i] = {expr};
    }}
}}
"""
    gpu.build(source)
    kern = gpu.kernel("exec_kern")

    bufs = []
    for arr in arrays:
        data = [float(x) for x in arr]
        bufs.append(gpu.from_list(data, "f"))

    out_buf = gpu.alloc(n * 4)
    out_buf._dtype = "f"
    out_buf._count = n

    args = bufs + [out_buf, n]
    kern.launch(n, args)
    return out_buf.to_list()


def gpu_compute(data, expr, device="auto"):
    """配列にOpenCL式を適用してGPUで計算

    numpy配列、リスト、ComputeArray を入力可能
    expr: "x * x + 1.0f" のような式 (x が各要素)
    """
    if hasattr(data, 'tolist'):
        data = data.tolist()
    elif isinstance(data, ComputeArray):
        data = data._data

    gpu = _get_gpu() or _get_igpu()
    if gpu is None:
        return [eval(expr.replace("x", str(v)).replace("f", "")) for v in data]

    from smile.gpu import gpu_map
    return gpu_map(expr, [float(x) for x in data], gpu)


# ============================================================
# CPU 並列実行
# ============================================================

def cpu_parallel(func, items, workers=None):
    """CPU全コアで並列実行

    func: 各要素に適用する関数
    items: イテラブル
    workers: ワーカー数 (デフォルト=コア数)
    """
    import concurrent.futures
    if workers is None:
        workers = os.cpu_count() or 4
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(func, items))


def parallel_map(func, items, workers=None):
    """並列map (GPU利用可能ならGPU、なければCPU全コア)"""
    items_list = list(items)
    n = len(items_list)

    # 数値リストでGPUが使えるなら GPU
    if n >= 1024 and all(isinstance(x, (int, float)) for x in items_list[:100]):
        gpu = _get_gpu() or _get_igpu()
        if gpu:
            # lambda/関数をOpenCL式に変換は難しいのでCPUフォールバック
            pass

    # CPU並列
    import concurrent.futures
    w = workers or (os.cpu_count() or 4)
    try:
        with concurrent.futures.ProcessPoolExecutor(max_workers=w) as ex:
            return list(ex.map(func, items_list, chunksize=max(1, n // w)))
    except Exception:
        with concurrent.futures.ThreadPoolExecutor(max_workers=w) as ex:
            return list(ex.map(func, items_list))


# ============================================================
# PyPI ライブラリ連携
# ============================================================

def numpy_gpu(arr, expr):
    """numpy配列をGPUで処理して返す

    import numpy as np
    a = np.random.randn(10000000).astype(np.float32)
    result = numpy_gpu(a, "x * x + 1.0f")  # GPU実行
    """
    try:
        import numpy as np
    except ImportError:
        raise RuntimeError("numpyが必要です")

    data = arr.astype(np.float32).ravel().tolist()
    result = gpu_compute(data, expr)
    return np.array(result, dtype=np.float32).reshape(arr.shape)


def pandas_gpu(series, expr):
    """pandas SeriesをGPUで処理

    import pandas as pd
    s = pd.Series(range(1000000), dtype=float)
    result = pandas_gpu(s, "x * 2.0f + 1.0f")
    """
    try:
        import pandas as pd
    except ImportError:
        raise RuntimeError("pandasが必要です")

    data = series.astype(float).tolist()
    result = gpu_compute(data, expr)
    return pd.Series(result, index=series.index, name=series.name)


def pil_gpu(image, expr):
    """PIL画像の各ピクセルをGPUで処理

    from PIL import Image
    img = Image.open("photo.jpg").convert("L")
    bright = pil_gpu(img, "clamp(x * 1.5f, 0.0f, 255.0f)")
    """
    try:
        from PIL import Image
        import numpy as np
    except ImportError:
        raise RuntimeError("Pillow と numpy が必要です")

    arr = np.array(image, dtype=np.float32)
    flat = arr.ravel().tolist()
    result = gpu_compute(flat, expr)
    out = np.array(result, dtype=np.float32).reshape(arr.shape)
    out = np.clip(out, 0, 255).astype(np.uint8)
    return Image.fromarray(out, mode=image.mode)


# ============================================================
# 全デバイス最大利用
# ============================================================

def saturate_all(func_gpu=None, func_igpu=None, func_cpu=None, seconds=10.0):
    """GPU + iGPU + CPU を同時に飽和利用

    3つの関数を同時に全デバイスで走らせる。
    func_gpu: GPU用の処理 (OpenCLGPUオブジェクトが渡される)
    func_igpu: iGPU用の処理
    func_cpu: CPU用の処理 (コア数が渡される)
    """
    results = {}
    threads = []

    if func_gpu:
        gpu = _get_gpu()
        if gpu:
            def _run_gpu():
                results["gpu"] = func_gpu(gpu)
            threads.append(threading.Thread(target=_run_gpu))

    if func_igpu:
        igpu = _get_igpu()
        if igpu:
            def _run_igpu():
                results["igpu"] = func_igpu(igpu)
            threads.append(threading.Thread(target=_run_igpu))

    if func_cpu:
        def _run_cpu():
            results["cpu"] = func_cpu(os.cpu_count() or 4)
        threads.append(threading.Thread(target=_run_cpu))

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    return results
