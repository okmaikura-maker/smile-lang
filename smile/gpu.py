"""Smile GPU モジュール - nvcuda.dll / OpenCL.dll 直叩き

CuPy・PyTorch・CUDA Toolkit 一切不要。
ドライバ同梱のDLLだけで GPU を最大限に使う。

対応:
  - NVIDIA GPU: nvcuda.dll (CUDA Driver API) → PTXカーネル
  - Intel/AMD iGPU + 全GPU: OpenCL.dll → OpenCL Cカーネル
  - SVM (Shared Virtual Memory): iGPUでゼロコピー転送
"""

import ctypes
import ctypes.util
import sys
import struct
import time
import array

_is_windows = sys.platform == "win32"
P = ctypes.c_void_p
_SZ = ctypes.c_size_t


# ============================================================
# CUDA バックエンド (nvcuda.dll 直叩き)
# ============================================================

_cuda = None
_cuda_inited = False

def _load_cuda():
    global _cuda, _cuda_inited
    if _cuda_inited:
        return _cuda
    _cuda_inited = True
    try:
        if _is_windows:
            k32 = ctypes.WinDLL("kernel32", use_last_error=True)
            _LoadLib = k32.LoadLibraryW
            _LoadLib.restype = ctypes.c_void_p
            _LoadLib.argtypes = [ctypes.c_wchar_p]
            _GetProc = k32.GetProcAddress
            _GetProc.restype = ctypes.c_void_p
            _GetProc.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
            hmod = _LoadLib("nvcuda.dll")
            if not hmod:
                return None
        else:
            return None

        class CudaDriver:
            def __init__(self, hmod):
                self.hmod = hmod
                self._cache = {}

            def _fn(self, name, restype, argtypes):
                if name in self._cache:
                    return self._cache[name]
                addr = _GetProc(self.hmod, name.encode("ascii"))
                if not addr:
                    return None
                proto = ctypes.CFUNCTYPE(restype, *argtypes)
                fn = proto(addr)
                self._cache[name] = fn
                return fn

            def check(self, code, where=""):
                if code != 0:
                    raise RuntimeError(f"CUDAエラー: {where} (code={code})")

        drv = CudaDriver(hmod)

        # 基本API解決
        CUresult = ctypes.c_int
        cuInit = drv._fn("cuInit", CUresult, [ctypes.c_uint])
        if cuInit is None:
            return None
        drv.check(cuInit(0), "cuInit")

        drv.cuDeviceGetCount = drv._fn("cuDeviceGetCount", CUresult, [P])
        drv.cuDeviceGet = drv._fn("cuDeviceGet", CUresult, [P, ctypes.c_int])
        drv.cuDeviceGetName = drv._fn("cuDeviceGetName", CUresult,
                                       [ctypes.c_char_p, ctypes.c_int, ctypes.c_int])
        drv.cuDeviceTotalMem = drv._fn("cuDeviceTotalMem_v2", CUresult, [P, ctypes.c_int])
        drv.cuDeviceGetAttribute = drv._fn("cuDeviceGetAttribute", CUresult,
                                            [P, ctypes.c_int, ctypes.c_int])
        drv.cuCtxCreate = drv._fn("cuCtxCreate_v2", CUresult, [P, ctypes.c_uint, ctypes.c_int])
        drv.cuCtxDestroy = drv._fn("cuCtxDestroy_v2", CUresult, [P])
        drv.cuCtxSynchronize = drv._fn("cuCtxSynchronize", CUresult, [])
        drv.cuMemAlloc = drv._fn("cuMemAlloc_v2", CUresult, [P, _SZ])
        drv.cuMemFree = drv._fn("cuMemFree_v2", CUresult, [ctypes.c_uint64])
        drv.cuMemcpyHtoD = drv._fn("cuMemcpyHtoD_v2", CUresult,
                                     [ctypes.c_uint64, P, _SZ])
        drv.cuMemcpyDtoH = drv._fn("cuMemcpyDtoH_v2", CUresult,
                                     [P, ctypes.c_uint64, _SZ])
        drv.cuMemsetD8 = drv._fn("cuMemsetD8_v2", CUresult,
                                   [ctypes.c_uint64, ctypes.c_ubyte, _SZ])
        drv.cuModuleLoadData = drv._fn("cuModuleLoadData", CUresult, [P, P])
        drv.cuModuleGetFunction = drv._fn("cuModuleGetFunction", CUresult,
                                           [P, P, ctypes.c_char_p])
        drv.cuLaunchKernel = drv._fn("cuLaunchKernel", CUresult,
                                      [P, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint,
                                       ctypes.c_uint, ctypes.c_uint, ctypes.c_uint,
                                       ctypes.c_uint, P, P, P])
        drv.cuMemGetInfo = drv._fn("cuMemGetInfo_v2", CUresult, [P, P])
        drv.cuMemAllocManaged = drv._fn("cuMemAllocManaged", CUresult,
                                         [P, _SZ, ctypes.c_uint])

        _cuda = drv
        return drv
    except Exception:
        return None


# ============================================================
# OpenCL バックエンド (OpenCL.dll 直叩き)
# ============================================================

_ocl = None
_ocl_inited = False

def _load_opencl():
    global _ocl, _ocl_inited
    if _ocl_inited:
        return _ocl
    _ocl_inited = True
    try:
        if _is_windows:
            cl = ctypes.WinDLL("OpenCL")
        else:
            path = ctypes.util.find_library("OpenCL")
            if not path:
                return None
            cl = ctypes.CDLL(path)

        for _n, _a in [
            ("clGetPlatformIDs", [ctypes.c_uint, P, P]),
            ("clGetPlatformInfo", [P, ctypes.c_uint, _SZ, P, P]),
            ("clGetDeviceIDs", [P, ctypes.c_ulonglong, ctypes.c_uint, P, P]),
            ("clGetDeviceInfo", [P, ctypes.c_uint, _SZ, P, P]),
            ("clCreateContext", [P, ctypes.c_uint, P, P, P, P]),
            ("clCreateCommandQueue", [P, P, ctypes.c_ulonglong, P]),
            ("clCreateProgramWithSource", [P, ctypes.c_uint, P, P, P]),
            ("clBuildProgram", [P, ctypes.c_uint, P, ctypes.c_char_p, P, P]),
            ("clGetProgramBuildInfo", [P, P, ctypes.c_uint, _SZ, P, P]),
            ("clCreateKernel", [P, ctypes.c_char_p, P]),
            ("clCreateBuffer", [P, ctypes.c_ulonglong, _SZ, P, P]),
            ("clSetKernelArg", [P, ctypes.c_uint, _SZ, P]),
            ("clEnqueueNDRangeKernel", [P, P, ctypes.c_uint, P, P, P, ctypes.c_uint, P, P]),
            ("clEnqueueWriteBuffer", [P, P, ctypes.c_uint, _SZ, _SZ, P, ctypes.c_uint, P, P]),
            ("clEnqueueReadBuffer", [P, P, ctypes.c_uint, _SZ, _SZ, P, ctypes.c_uint, P, P]),
            ("clFinish", [P]),
            ("clReleaseKernel", [P]),
            ("clReleaseProgram", [P]),
            ("clReleaseMemObject", [P]),
            ("clReleaseCommandQueue", [P]),
            ("clReleaseContext", [P]),
        ]:
            f = getattr(cl, _n)
            f.restype = ctypes.c_int if _n.startswith(("clGet", "clBuild", "clSet",
                         "clEnqueue", "clFinish", "clRelease")) else P
            f.argtypes = _a
        for _n in ("clCreateContext", "clCreateCommandQueue",
                   "clCreateProgramWithSource", "clCreateKernel", "clCreateBuffer"):
            getattr(cl, _n).restype = P

        # SVM (optional)
        for _n, _a, _ret in [
            ("clSVMAlloc", [P, ctypes.c_ulonglong, _SZ, ctypes.c_uint], P),
            ("clSVMFree", [P, P], None),
            ("clSetKernelArgSVMPointer", [P, ctypes.c_uint, P], ctypes.c_int),
            ("clEnqueueSVMMap", [P, ctypes.c_uint, ctypes.c_ulonglong, P, _SZ,
                                 ctypes.c_uint, P, P], ctypes.c_int),
            ("clEnqueueSVMUnmap", [P, P, ctypes.c_uint, P, P], ctypes.c_int),
        ]:
            try:
                _f = getattr(cl, _n)
                _f.argtypes = _a
                if _ret is not None:
                    _f.restype = _ret
            except AttributeError:
                pass

        _ocl = cl
        return cl
    except Exception:
        return None


# ============================================================
# Smile API: gpu_devices() - 全GPU列挙
# ============================================================

def gpu_devices():
    """全てのGPU/iGPUを列挙する。NVIDIA + OpenCL 両方。"""
    results = []

    # CUDA (NVIDIA)
    drv = _load_cuda()
    if drv:
        count = ctypes.c_int()
        drv.check(drv.cuDeviceGetCount(ctypes.byref(count)), "cuDeviceGetCount")
        for i in range(count.value):
            dev = ctypes.c_int()
            drv.check(drv.cuDeviceGet(ctypes.byref(dev), i), "cuDeviceGet")
            name = ctypes.create_string_buffer(256)
            drv.check(drv.cuDeviceGetName(name, 256, dev.value), "cuDeviceGetName")
            mem = ctypes.c_size_t()
            drv.check(drv.cuDeviceTotalMem(ctypes.byref(mem), dev.value), "cuDeviceTotalMem")
            results.append({
                "index": i,
                "name": name.value.decode(),
                "memory_mb": mem.value // (1024 * 1024),
                "backend": "cuda",
                "vendor": "NVIDIA",
            })

    # OpenCL (全ベンダ)
    cl = _load_opencl()
    if cl:
        n = ctypes.c_uint()
        cl.clGetPlatformIDs(0, None, ctypes.byref(n))
        if n.value > 0:
            plats = (P * n.value)()
            cl.clGetPlatformIDs(n.value, plats, None)
            idx = 0
            for pi in range(n.value):
                p = plats[pi]
                sz = _SZ()
                cl.clGetPlatformInfo(p, 0x0902, 0, None, ctypes.byref(sz))
                buf = ctypes.create_string_buffer(sz.value)
                cl.clGetPlatformInfo(p, 0x0902, sz.value, buf, None)
                pname = buf.value.decode(errors="replace")

                nd = ctypes.c_uint()
                if cl.clGetDeviceIDs(p, 0xFFFFFFFF, 0, None, ctypes.byref(nd)) != 0:
                    continue
                devs = (P * nd.value)()
                cl.clGetDeviceIDs(p, 0xFFFFFFFF, nd.value, devs, None)
                for di in range(nd.value):
                    d = devs[di]
                    sz2 = _SZ()
                    cl.clGetDeviceInfo(d, 0x102B, 0, None, ctypes.byref(sz2))
                    nbuf = ctypes.create_string_buffer(sz2.value)
                    cl.clGetDeviceInfo(d, 0x102B, sz2.value, nbuf, None)
                    dname = nbuf.value.decode(errors="replace")

                    t = ctypes.c_ulonglong()
                    cl.clGetDeviceInfo(d, 0x1000, 8, ctypes.byref(t), None)
                    kind_map = {4: "GPU", 2: "CPU", 8: "ACCEL", 1: "DEFAULT"}
                    kind = kind_map.get(t.value, str(t.value))

                    cu = ctypes.c_uint()
                    cl.clGetDeviceInfo(d, 0x1002, 4, ctypes.byref(cu), None)

                    gmem = ctypes.c_uint64()
                    cl.clGetDeviceInfo(d, 0x101F, 8, ctypes.byref(gmem), None)

                    vendor = ("Intel" if "Intel" in pname else
                              "AMD" if "AMD" in pname or "Advanced" in pname else
                              "NVIDIA" if "NVIDIA" in pname else pname)

                    results.append({
                        "index": idx,
                        "name": dname,
                        "kind": kind,
                        "compute_units": cu.value,
                        "memory_mb": gmem.value // (1024 * 1024),
                        "backend": "opencl",
                        "vendor": vendor,
                        "platform": pname,
                        "_handle": devs[di],
                    })
                    idx += 1

    return results


# ============================================================
# CUDAコンテキスト
# ============================================================

class CudaGPU:
    """NVIDIA GPU を nvcuda.dll で直接制御する。"""

    def __init__(self, device_index=0):
        drv = _load_cuda()
        if not drv:
            raise RuntimeError("CUDAエラー: nvcuda.dll が見つかりません。NVIDIAドライバを確認してください。")
        self.drv = drv
        dev = ctypes.c_int()
        drv.check(drv.cuDeviceGet(ctypes.byref(dev), device_index), "cuDeviceGet")
        self.dev = dev.value

        name = ctypes.create_string_buffer(256)
        drv.check(drv.cuDeviceGetName(name, 256, self.dev), "cuDeviceGetName")
        self.name = name.value.decode()

        ctx = P()
        drv.check(drv.cuCtxCreate(ctypes.byref(ctx), 4, self.dev), "cuCtxCreate")
        self.ctx = ctx

    def alloc(self, nbytes):
        """GPUメモリを確保する。"""
        ptr = ctypes.c_uint64()
        self.drv.check(self.drv.cuMemAlloc(ctypes.byref(ptr), nbytes), "cuMemAlloc")
        return CudaBuffer(self, ptr.value, nbytes)

    def from_list(self, data, dtype="f"):
        """Pythonリストからデータを送り込む。dtype: 'f'=float32, 'd'=float64, 'i'=int32"""
        arr = array.array(dtype, data)
        buf = self.alloc(len(arr) * arr.itemsize)
        c_data = (ctypes.c_char * len(arr.tobytes())).from_buffer_copy(arr.tobytes())
        self.drv.check(self.drv.cuMemcpyHtoD(buf.ptr, c_data, len(arr.tobytes())), "H2D")
        buf._dtype = dtype
        buf._count = len(data)
        return buf

    def memset(self, buf, value=0):
        """GPUメモリを指定値で埋める。"""
        self.drv.check(self.drv.cuMemsetD8(buf.ptr, value & 0xFF, buf.nbytes), "cuMemsetD8")

    def mem_info(self):
        """空き/合計メモリ(bytes)を返す。"""
        free = ctypes.c_size_t()
        total = ctypes.c_size_t()
        self.drv.check(self.drv.cuMemGetInfo(ctypes.byref(free), ctypes.byref(total)), "cuMemGetInfo")
        return {"free_mb": free.value // (1024*1024), "total_mb": total.value // (1024*1024)}

    def load_ptx(self, ptx_source):
        """PTXソースコードからモジュールをロードする。"""
        if isinstance(ptx_source, str):
            ptx_source = ptx_source.encode("utf-8")
        mod = P()
        self.drv.check(self.drv.cuModuleLoadData(ctypes.byref(mod), ptx_source), "cuModuleLoadData")
        return CudaModule(self, mod)

    def sync(self):
        """GPU処理の完了を待つ。"""
        self.drv.check(self.drv.cuCtxSynchronize(), "cuCtxSynchronize")

    def close(self):
        if self.ctx:
            self.drv.cuCtxDestroy(self.ctx)
            self.ctx = None

    def __repr__(self):
        return f"CudaGPU({self.name})"

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


class CudaBuffer:
    """CUDA GPUメモリバッファ。"""

    def __init__(self, gpu, ptr, nbytes):
        self.gpu = gpu
        self.ptr = ptr
        self.nbytes = nbytes
        self._dtype = "f"
        self._count = nbytes // 4

    def to_list(self, dtype=None, count=None):
        """GPU→Pythonリスト。"""
        dtype = dtype or self._dtype
        count = count or self._count
        itemsize = array.array(dtype, [0]).itemsize
        nbytes = count * itemsize
        c_buf = (ctypes.c_char * nbytes)()
        self.gpu.drv.check(self.gpu.drv.cuMemcpyDtoH(c_buf, self.ptr, nbytes), "D2H")
        arr = array.array(dtype)
        arr.frombytes(bytes(c_buf))
        return arr.tolist()

    def free(self):
        if self.ptr:
            self.gpu.drv.cuMemFree(self.ptr)
            self.ptr = 0

    def __repr__(self):
        return f"CudaBuffer({self.nbytes} bytes)"

    def __del__(self):
        try:
            self.free()
        except Exception:
            pass


class CudaModule:
    """PTXモジュール。"""

    def __init__(self, gpu, mod):
        self.gpu = gpu
        self.mod = mod

    def get_kernel(self, name):
        """カーネル関数を取得する。"""
        func = P()
        self.gpu.drv.check(self.gpu.drv.cuModuleGetFunction(
            ctypes.byref(func), self.mod, name.encode("ascii")), "cuModuleGetFunction")
        return CudaKernel(self.gpu, func)


class CudaKernel:
    """CUDAカーネル。"""

    def __init__(self, gpu, func):
        self.gpu = gpu
        self.func = func

    def launch(self, grid, block, args, shared_mem=0):
        """カーネルを起動する。
        grid: (gx, gy, gz) or int
        block: (bx, by, bz) or int
        args: [CudaBuffer, int, float, ...]
        """
        if isinstance(grid, int):
            grid = (grid, 1, 1)
        if isinstance(block, int):
            block = (block, 1, 1)

        # 引数パック
        arg_ptrs = []
        arg_values = []
        for a in args:
            if isinstance(a, CudaBuffer):
                v = ctypes.c_uint64(a.ptr)
                arg_values.append(v)
                arg_ptrs.append(ctypes.cast(ctypes.pointer(v), P))
            elif isinstance(a, float):
                v = ctypes.c_float(a)
                arg_values.append(v)
                arg_ptrs.append(ctypes.cast(ctypes.pointer(v), P))
            elif isinstance(a, int):
                v = ctypes.c_int(a)
                arg_values.append(v)
                arg_ptrs.append(ctypes.cast(ctypes.pointer(v), P))

        arg_arr = (P * len(arg_ptrs))(*arg_ptrs)
        self.gpu.drv.check(self.gpu.drv.cuLaunchKernel(
            self.func,
            grid[0], grid[1], grid[2],
            block[0], block[1], block[2],
            shared_mem, None, arg_arr, None
        ), "cuLaunchKernel")


# ============================================================
# OpenCLコンテキスト
# ============================================================

class OpenCLGPU:
    """OpenCL GPU/iGPU を OpenCL.dll で直接制御する。"""

    def __init__(self, device_index=0):
        cl = _load_opencl()
        if not cl:
            raise RuntimeError("OpenCLエラー: OpenCL.dll が見つかりません。")
        self.cl = cl
        devs = gpu_devices()
        ocl_devs = [d for d in devs if d["backend"] == "opencl"]
        if device_index >= len(ocl_devs):
            raise RuntimeError(f"OpenCLデバイス {device_index} が見つかりません (見つかったのは {len(ocl_devs)} 台)")
        d = ocl_devs[device_index]
        self.name = d["name"]
        self.vendor = d["vendor"]
        self._handle = d["_handle"]

        err = ctypes.c_int()
        dev = P(self._handle)
        self.ctx = cl.clCreateContext(None, 1, ctypes.byref(dev), None, None, ctypes.byref(err))
        self.q = cl.clCreateCommandQueue(self.ctx, dev, 0, ctypes.byref(err))
        self.dev = dev
        self._prog = None

    def alloc(self, nbytes):
        """GPUメモリを確保する。"""
        err = ctypes.c_int()
        mem = self.cl.clCreateBuffer(self.ctx, 1, max(nbytes, 1), None, ctypes.byref(err))
        return CLBuffer(self, mem, nbytes)

    def from_list(self, data, dtype="f"):
        """Pythonリストからデータを送り込む。"""
        arr = array.array(dtype, data)
        buf = self.alloc(len(arr) * arr.itemsize)
        raw = arr.tobytes()
        c_data = (ctypes.c_char * len(raw)).from_buffer_copy(raw)
        self.cl.clEnqueueWriteBuffer(self.q, buf.mem, 1, 0, len(raw), c_data, 0, None, None)
        buf._dtype = dtype
        buf._count = len(data)
        return buf

    def build(self, source):
        """OpenCL Cソースコードをビルドする。"""
        if isinstance(source, str):
            source = source.encode()
        err = ctypes.c_int()
        src = ctypes.c_char_p(source)
        ln = _SZ(len(source))
        prog = self.cl.clCreateProgramWithSource(
            self.ctx, 1, ctypes.byref(src), ctypes.byref(ln), ctypes.byref(err))
        ret = self.cl.clBuildProgram(prog, 1, ctypes.byref(self.dev), None, None, None)
        if ret != 0:
            log_buf = ctypes.create_string_buffer(4096)
            self.cl.clGetProgramBuildInfo(prog, self.dev, 0x1183, 4096, log_buf, None)
            raise RuntimeError(f"OpenCLビルドエラー:\n{log_buf.value.decode(errors='replace')}")
        self._prog = prog
        return self

    def kernel(self, name):
        """ビルド済みプログラムからカーネルを取得する。"""
        if not self._prog:
            raise RuntimeError("先にbuild()でソースをビルドしてください。")
        err = ctypes.c_int()
        k = self.cl.clCreateKernel(self._prog, name.encode(), ctypes.byref(err))
        return CLKernel(self, k)

    def sync(self):
        """GPU処理の完了を待つ。"""
        self.cl.clFinish(self.q)

    def close(self):
        if self.q:
            self.cl.clReleaseCommandQueue(P(self.q))
            self.q = None
        if self.ctx:
            self.cl.clReleaseContext(P(self.ctx))
            self.ctx = None

    def __repr__(self):
        return f"OpenCLGPU({self.name}, {self.vendor})"

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


class CLBuffer:
    """OpenCL GPUメモリバッファ。"""

    def __init__(self, gpu, mem, nbytes):
        self.gpu = gpu
        self.mem = mem
        self.nbytes = nbytes
        self._dtype = "f"
        self._count = nbytes // 4

    def to_list(self, dtype=None, count=None):
        """GPU→Pythonリスト。"""
        dtype = dtype or self._dtype
        count = count or self._count
        itemsize = array.array(dtype, [0]).itemsize
        nbytes = count * itemsize
        c_buf = (ctypes.c_char * nbytes)()
        self.gpu.cl.clEnqueueReadBuffer(self.gpu.q, self.mem, 1, 0, nbytes, c_buf, 0, None, None)
        arr = array.array(dtype)
        arr.frombytes(bytes(c_buf))
        return arr.tolist()

    def __repr__(self):
        return f"CLBuffer({self.nbytes} bytes)"


class CLKernel:
    """OpenCLカーネル。"""

    def __init__(self, gpu, kern):
        self.gpu = gpu
        self.k = kern

    def launch(self, global_size, args, sync=True):
        """カーネルを起動する。
        global_size: int (ワークアイテム数)
        args: [CLBuffer, int, float, ...]
        """
        for i, a in enumerate(args):
            if isinstance(a, CLBuffer):
                self.gpu.cl.clSetKernelArg(self.k, i, ctypes.sizeof(P), ctypes.byref(P(a.mem)))
            elif isinstance(a, float):
                v = ctypes.c_float(a)
                self.gpu.cl.clSetKernelArg(self.k, i, 4, ctypes.byref(v))
            elif isinstance(a, int):
                v = ctypes.c_int(a)
                self.gpu.cl.clSetKernelArg(self.k, i, 4, ctypes.byref(v))
        g = (_SZ * 1)(int(global_size))
        self.gpu.cl.clEnqueueNDRangeKernel(self.gpu.q, self.k, 1, None, g, None, 0, None, None)
        if sync:
            self.gpu.cl.clFinish(self.gpu.q)


# ============================================================
# 統合API: gpu_auto() - 最適なGPUを自動選択
# ============================================================

def gpu_auto():
    """利用可能な最適なGPUを自動選択して返す。
    NVIDIA GPU があれば CudaGPU、なければ OpenCL のGPU/iGPU を返す。
    """
    drv = _load_cuda()
    if drv:
        count = ctypes.c_int()
        drv.check(drv.cuDeviceGetCount(ctypes.byref(count)), "cuDeviceGetCount")
        if count.value > 0:
            return CudaGPU(0)

    cl = _load_opencl()
    if cl:
        devs = gpu_devices()
        ocl_gpus = [d for d in devs if d["backend"] == "opencl" and d.get("kind") == "GPU"]
        if ocl_gpus:
            return OpenCLGPU(0)

    raise RuntimeError("GPUが見つかりません。NVIDIAドライバまたはOpenCLランタイムをインストールしてください。")


# ============================================================
# ベンチマーク
# ============================================================

def gpu_bench(gpu=None, size=1024*1024, iters=1000):
    """GPUの性能をベンチマークする。GFLOPS を返す。"""
    if gpu is None:
        gpu = gpu_auto()

    # CUDAもOpenCL Cカーネルで統一（PTXはGPUアーキ依存で面倒）
    if isinstance(gpu, CudaGPU):
        # CUDAの場合はOpenCLデバイスにフォールバックしてベンチ
        cl = _load_opencl()
        if cl:
            try:
                ocl_gpu = OpenCLGPU(0)
                result = gpu_bench(ocl_gpu, size, iters)
                result["gpu"] = gpu.name
                result["backend"] = "cuda+opencl"
                return result
            except Exception:
                pass
        return {"gpu": gpu.name, "backend": "cuda", "gflops": 0, "note": "OpenCLフォールバック不可"}

    if isinstance(gpu, OpenCLGPU):
        source = """
__kernel void bench(__global float* out, const int iters) {
    int i = get_global_id(0);
    float a = i * 1e-6f, b = a + 0.1f;
    for (int k = 0; k < iters; k++) {
        a = a * 0.9f + 0.1f;
        b = b * 0.9f + 0.1f;
    }
    out[i] = a + b;
}
"""
        gpu.build(source)
        kern = gpu.kernel("bench")
        buf = gpu.alloc(size * 4)
        t0 = time.perf_counter()
        for _ in range(3):
            kern.launch(size, [buf, iters])
        gpu.sync()
        dt = time.perf_counter() - t0
        flop = 3 * size * iters * 4
        return {"gpu": gpu.name, "backend": "opencl",
                "gflops": flop / dt / 1e9, "seconds": dt}


# ============================================================
# 便利関数: gpu_map / gpu_reduce
# ============================================================

def gpu_map(func_source, data, gpu=None):
    """リストの各要素にGPUカーネルを適用する。
    func_source: OpenCL C の式（変数 x に入力値が入る）
    data: float のリスト
    例: gpu_map("x * x + 1.0f", [1.0, 2.0, 3.0])
    """
    if gpu is None:
        gpu = gpu_auto()

    n = len(data)
    if isinstance(gpu, OpenCLGPU):
        source = f"""
__kernel void map_kern(__global const float* in, __global float* out, const int n) {{
    int i = get_global_id(0);
    if (i < n) {{
        float x = in[i];
        out[i] = {func_source};
    }}
}}
"""
        gpu.build(source)
        kern = gpu.kernel("map_kern")
        in_buf = gpu.from_list(data, "f")
        out_buf = gpu.alloc(n * 4)
        out_buf._dtype = "f"
        out_buf._count = n
        kern.launch(n, [in_buf, out_buf, n])
        return out_buf.to_list()

    elif isinstance(gpu, CudaGPU):
        cl = _load_opencl()
        if cl:
            ocl_gpu = OpenCLGPU(0)
            return gpu_map(func_source, data, ocl_gpu)
        raise RuntimeError("gpu_map()にはOpenCLが必要です。")


def gpu_sum(data, gpu=None):
    """リストの合計をGPUで計算する。"""
    if gpu is None:
        gpu = gpu_auto()

    n = len(data)
    if isinstance(gpu, OpenCLGPU):
        source = """
__kernel void partial_sum(__global const float* in, __global float* out,
                          const int n, const int chunk) {
    int gid = get_global_id(0);
    int start = gid * chunk;
    int end = start + chunk;
    if (end > n) end = n;
    float s = 0.0f;
    for (int i = start; i < end; i++) s += in[i];
    out[gid] = s;
}
"""
        gpu.build(source)
        kern = gpu.kernel("partial_sum")
        groups = min(n, 256)
        chunk = (n + groups - 1) // groups
        in_buf = gpu.from_list(data, "f")
        out_buf = gpu.alloc(groups * 4)
        out_buf._dtype = "f"
        out_buf._count = groups
        kern.launch(groups, [in_buf, out_buf, n, chunk])
        partial = out_buf.to_list()
        return sum(partial)
    else:
        return sum(data)
