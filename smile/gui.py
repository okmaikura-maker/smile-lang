"""Smile GUI - Win32 GDI直叩きキャンバス

WebView2なし、依存ゼロ。user32.dll + gdi32.dll のみ。
ウィンドウ作成、描画、イベント処理をSmile標準関数で提供。

使い方:
  win = window("タイトル", 800, 600)
  win.fill("white")
  win.rect(10, 10, 200, 100, "blue")
  win.text(20, 30, "Hello GUI!", size=24)
  win.circle(400, 300, 50, "red")
  win.show()

  while win.is_open() {
      ev = win.poll()
      if ev != none {
          if ev.type == "click" { ... }
          if ev.type == "key" { ... }
      }
      win.update()
  }
"""

import sys
import ctypes
import ctypes.wintypes as wt
import struct
import threading
import time

if sys.platform != "win32":
    raise ImportError("GUIモジュールはWindowsのみ対応です")

# ============================================================
# Win32 定数
# ============================================================
WS_OVERLAPPEDWINDOW = 0x00CF0000
WS_VISIBLE = 0x10000000
WS_CLIPCHILDREN = 0x02000000
CW_USEDEFAULT = -2147483648
CS_HREDRAW = 0x0002
CS_VREDRAW = 0x0001
CS_OWNDC = 0x0020

WM_DESTROY = 0x0002
WM_PAINT = 0x000F
WM_CLOSE = 0x0010
WM_QUIT = 0x0012
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_CHAR = 0x0102
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_RBUTTONDOWN = 0x0204
WM_RBUTTONUP = 0x0205
WM_MOUSEMOVE = 0x0200
WM_MOUSEWHEEL = 0x020A
WM_SIZE = 0x0005
WM_ERASEBKGND = 0x0014
WM_TIMER = 0x0113

PM_REMOVE = 0x0001
DT_LEFT = 0x0000
DT_CENTER = 0x0001
DT_VCENTER = 0x0004
DT_SINGLELINE = 0x0020

SRCCOPY = 0x00CC0020
DIB_RGB_COLORS = 0

TRANSPARENT = 1

IDC_ARROW = 32512

MK_LBUTTON = 0x0001
MK_RBUTTON = 0x0002

VK_MAP = {
    0x1B: "escape", 0x0D: "enter", 0x20: "space", 0x08: "backspace",
    0x09: "tab", 0x25: "left", 0x26: "up", 0x27: "right", 0x28: "down",
    0x2E: "delete", 0x24: "home", 0x23: "end",
    0x21: "pageup", 0x22: "pagedown",
    0x70: "f1", 0x71: "f2", 0x72: "f3", 0x73: "f4",
    0x74: "f5", 0x75: "f6", 0x76: "f7", 0x77: "f8",
    0x78: "f9", 0x79: "f10", 0x7A: "f11", 0x7B: "f12",
    0x10: "shift", 0x11: "ctrl", 0x12: "alt",
}

# ============================================================
# Win32 API
# ============================================================
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
kernel32 = ctypes.windll.kernel32

LRESULT = ctypes.c_ssize_t

user32.DefWindowProcW.argtypes = [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]
user32.DefWindowProcW.restype = LRESULT
user32.CreateWindowExW.argtypes = [
    wt.DWORD, wt.LPCWSTR, wt.LPCWSTR, wt.DWORD,
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    wt.HWND, wt.HANDLE, wt.HINSTANCE, ctypes.c_void_p,
]
user32.CreateWindowExW.restype = wt.HWND
user32.PeekMessageW.argtypes = [ctypes.POINTER(wt.MSG), wt.HWND, wt.UINT, wt.UINT, wt.UINT]
user32.PeekMessageW.restype = wt.BOOL
user32.AdjustWindowRect.argtypes = [ctypes.POINTER(wt.RECT), wt.DWORD, wt.BOOL]
user32.AdjustWindowRect.restype = wt.BOOL
user32.GetDC.restype = wt.HDC
user32.GetDC.argtypes = [wt.HWND]
user32.ReleaseDC.argtypes = [wt.HWND, wt.HDC]
user32.ReleaseDC.restype = ctypes.c_int
user32.ShowWindow.argtypes = [wt.HWND, ctypes.c_int]
user32.ShowWindow.restype = wt.BOOL
user32.UpdateWindow.argtypes = [wt.HWND]
user32.UpdateWindow.restype = wt.BOOL
user32.DestroyWindow.argtypes = [wt.HWND]
user32.DestroyWindow.restype = wt.BOOL
user32.PostQuitMessage.argtypes = [ctypes.c_int]
user32.PostQuitMessage.restype = None
user32.TranslateMessage.argtypes = [ctypes.POINTER(wt.MSG)]
user32.TranslateMessage.restype = wt.BOOL
user32.DispatchMessageW.argtypes = [ctypes.POINTER(wt.MSG)]
user32.DispatchMessageW.restype = LRESULT
user32.LoadCursorW.argtypes = [wt.HINSTANCE, wt.LPCWSTR]
user32.LoadCursorW.restype = wt.HANDLE
user32.DrawTextW.argtypes = [wt.HDC, wt.LPCWSTR, ctypes.c_int, ctypes.POINTER(wt.RECT), wt.UINT]
user32.DrawTextW.restype = ctypes.c_int
user32.SetWindowTextW.argtypes = [wt.HWND, wt.LPCWSTR]
user32.SetWindowTextW.restype = wt.BOOL
gdi32.CreateCompatibleDC.argtypes = [wt.HDC]
gdi32.CreateCompatibleDC.restype = wt.HDC
gdi32.DeleteDC.argtypes = [wt.HDC]
gdi32.DeleteDC.restype = wt.BOOL
gdi32.DeleteObject.argtypes = [wt.HANDLE]
gdi32.DeleteObject.restype = wt.BOOL
gdi32.SelectObject.argtypes = [wt.HDC, wt.HANDLE]
gdi32.SelectObject.restype = wt.HANDLE
gdi32.BitBlt.argtypes = [wt.HDC, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                         wt.HDC, ctypes.c_int, ctypes.c_int, wt.DWORD]
gdi32.BitBlt.restype = wt.BOOL
gdi32.CreateDIBSection.argtypes = [wt.HDC, ctypes.c_void_p, wt.UINT,
                                   ctypes.POINTER(ctypes.c_void_p), wt.HANDLE, wt.DWORD]
gdi32.CreateDIBSection.restype = wt.HANDLE
gdi32.CreateFontW.argtypes = [
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    wt.DWORD, wt.DWORD, wt.DWORD, wt.DWORD, wt.DWORD,
    wt.DWORD, wt.DWORD, wt.DWORD, wt.LPCWSTR,
]
gdi32.CreateFontW.restype = wt.HANDLE
gdi32.SetTextColor.argtypes = [wt.HDC, wt.COLORREF]
gdi32.SetTextColor.restype = wt.COLORREF
gdi32.SetBkMode.argtypes = [wt.HDC, ctypes.c_int]
gdi32.SetBkMode.restype = ctypes.c_int
kernel32.GetModuleHandleW.argtypes = [wt.LPCWSTR]
kernel32.GetModuleHandleW.restype = wt.HMODULE

WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM)

class WNDCLASSEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wt.UINT),
        ("style", wt.UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wt.HINSTANCE),
        ("hIcon", wt.HICON),
        ("hCursor", wt.HANDLE),
        ("hbrBackground", wt.HBRUSH),
        ("lpszMenuName", wt.LPCWSTR),
        ("lpszClassName", wt.LPCWSTR),
        ("hIconSm", wt.HICON),
    ]

user32.RegisterClassExW.argtypes = [ctypes.POINTER(WNDCLASSEXW)]
user32.RegisterClassExW.restype = wt.ATOM

class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wt.DWORD),
        ("biWidth", ctypes.c_long),
        ("biHeight", ctypes.c_long),
        ("biPlanes", wt.WORD),
        ("biBitCount", wt.WORD),
        ("biCompression", wt.DWORD),
        ("biSizeImage", wt.DWORD),
        ("biXPelsPerMeter", ctypes.c_long),
        ("biYPelsPerMeter", ctypes.c_long),
        ("biClrUsed", wt.DWORD),
        ("biClrImportant", wt.DWORD),
    ]

class BITMAPINFO(ctypes.Structure):
    _fields_ = [
        ("bmiHeader", BITMAPINFOHEADER),
        ("bmiColors", wt.DWORD * 3),
    ]

# ============================================================
# 色変換
# ============================================================
_COLOR_MAP = {
    "black": (0, 0, 0), "white": (255, 255, 255),
    "red": (255, 0, 0), "green": (0, 180, 0), "blue": (0, 100, 255),
    "yellow": (255, 220, 0), "orange": (255, 140, 0), "purple": (140, 0, 200),
    "cyan": (0, 200, 200), "magenta": (255, 0, 255), "pink": (255, 130, 180),
    "gray": (140, 140, 140), "grey": (140, 140, 140),
    "darkgray": (80, 80, 80), "lightgray": (200, 200, 200),
    "brown": (139, 69, 19), "navy": (0, 0, 128), "teal": (0, 128, 128),
    "lime": (0, 255, 0), "gold": (255, 215, 0), "silver": (192, 192, 192),
    "skyblue": (100, 180, 255), "coral": (255, 100, 80),
}

def _parse_color(c):
    if isinstance(c, (list, tuple)) and len(c) >= 3:
        return (int(c[0]), int(c[1]), int(c[2]))
    if isinstance(c, str):
        c = c.lower().strip()
        if c in _COLOR_MAP:
            return _COLOR_MAP[c]
        if c.startswith("#") and len(c) == 7:
            return (int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16))
        if c.startswith("#") and len(c) == 4:
            return (int(c[1]*2, 16), int(c[2]*2, 16), int(c[3]*2, 16))
    return (0, 0, 0)

def _rgb(r, g, b):
    return r | (g << 8) | (b << 16)

def _colorref(c):
    r, g, b = _parse_color(c)
    return _rgb(r, g, b)


# ============================================================
# Canvas (ソフトウェアフレームバッファ)
# ============================================================
class Canvas:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.stride = w * 4
        self.buf = bytearray(w * h * 4)
        self._dirty = True

    def resize(self, w, h):
        self.w = w
        self.h = h
        self.stride = w * 4
        self.buf = bytearray(w * h * 4)
        self._dirty = True

    def _px(self, x, y, r, g, b, a=255):
        if 0 <= x < self.w and 0 <= y < self.h:
            off = (y * self.w + x) * 4
            if a >= 255:
                self.buf[off] = b
                self.buf[off+1] = g
                self.buf[off+2] = r
                self.buf[off+3] = 255
            else:
                old_b = self.buf[off]
                old_g = self.buf[off+1]
                old_r = self.buf[off+2]
                fa = a / 255.0
                ia = 1.0 - fa
                self.buf[off] = int(b * fa + old_b * ia)
                self.buf[off+1] = int(g * fa + old_g * ia)
                self.buf[off+2] = int(r * fa + old_r * ia)
                self.buf[off+3] = 255

    def clear(self, color="white"):
        r, g, b = _parse_color(color)
        row = bytes([b, g, r, 255]) * self.w
        for y in range(self.h):
            off = y * self.stride
            self.buf[off:off+self.stride] = row
        self._dirty = True

    def fill_rect(self, x, y, w, h, color):
        r, g, b = _parse_color(color)
        x, y = int(x), int(y)
        w, h = int(w), int(h)
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        pixel = bytes([b, g, r, 255])
        row = pixel * (x1 - x0)
        for py in range(y0, y1):
            off = py * self.stride + x0 * 4
            self.buf[off:off+len(row)] = row
        self._dirty = True

    def stroke_rect(self, x, y, w, h, color, thickness=1):
        t = int(thickness)
        self.fill_rect(x, y, w, t, color)
        self.fill_rect(x, y + h - t, w, t, color)
        self.fill_rect(x, y, t, h, color)
        self.fill_rect(x + w - t, y, t, h, color)
        self._dirty = True

    def line(self, x0, y0, x1, y1, color, thickness=1):
        r, g, b = _parse_color(color)
        x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        t = int(thickness) // 2
        while True:
            for tx in range(-t, t+1):
                for ty in range(-t, t+1):
                    self._px(x0+tx, y0+ty, r, g, b)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy
        self._dirty = True

    def circle(self, cx, cy, radius, color, fill=True):
        r, g, b = _parse_color(color)
        cx, cy, radius = int(cx), int(cy), int(radius)
        if fill:
            for y in range(-radius, radius+1):
                half = int((radius*radius - y*y) ** 0.5)
                py = cy + y
                if 0 <= py < self.h:
                    x0 = max(0, cx - half)
                    x1 = min(self.w, cx + half + 1)
                    pixel = bytes([b, g, r, 255])
                    row = pixel * (x1 - x0)
                    off = py * self.stride + x0 * 4
                    self.buf[off:off+len(row)] = row
        else:
            x, y = radius, 0
            err = 1 - radius
            while x >= y:
                for px, py in [(cx+x,cy+y),(cx-x,cy+y),(cx+x,cy-y),(cx-x,cy-y),
                                (cx+y,cy+x),(cx-y,cy+x),(cx+y,cy-x),(cx-y,cy-x)]:
                    self._px(px, py, r, g, b)
                y += 1
                if err < 0:
                    err += 2*y + 1
                else:
                    x -= 1
                    err += 2*(y-x) + 1
        self._dirty = True

    def triangle(self, x0, y0, x1, y1, x2, y2, color, fill=True):
        if fill:
            r, g, b = _parse_color(color)
            pts = sorted([(int(x0),int(y0)),(int(x1),int(y1)),(int(x2),int(y2))], key=lambda p:p[1])
            def interp(ya, xa, yb, xb, y):
                if yb == ya: return xa
                return xa + (xb - xa) * (y - ya) / (yb - ya)
            for y in range(max(0, pts[0][1]), min(self.h, pts[2][1]+1)):
                if y < pts[1][1]:
                    lx = interp(pts[0][1], pts[0][0], pts[2][1], pts[2][0], y)
                    rx = interp(pts[0][1], pts[0][0], pts[1][1], pts[1][0], y)
                else:
                    lx = interp(pts[0][1], pts[0][0], pts[2][1], pts[2][0], y)
                    rx = interp(pts[1][1], pts[1][0], pts[2][1], pts[2][0], y)
                if lx > rx:
                    lx, rx = rx, lx
                x0c = max(0, int(lx))
                x1c = min(self.w, int(rx)+1)
                pixel = bytes([b, g, r, 255])
                row = pixel * (x1c - x0c)
                off = y * self.stride + x0c * 4
                self.buf[off:off+len(row)] = row
        else:
            self.line(x0,y0,x1,y1,color)
            self.line(x1,y1,x2,y2,color)
            self.line(x2,y2,x0,y0,color)
        self._dirty = True

    def gradient_rect(self, x, y, w, h, color1, color2, vertical=True):
        r1,g1,b1 = _parse_color(color1)
        r2,g2,b2 = _parse_color(color2)
        x,y,w,h = int(x),int(y),int(w),int(h)
        steps = h if vertical else w
        for i in range(steps):
            t = i / max(1, steps - 1)
            cr = int(r1 + (r2-r1)*t)
            cg = int(g1 + (g2-g1)*t)
            cb = int(b1 + (b2-b1)*t)
            if vertical:
                self.fill_rect(x, y+i, w, 1, (cr,cg,cb))
            else:
                self.fill_rect(x+i, y, 1, h, (cr,cg,cb))
        self._dirty = True

    def rounded_rect(self, x, y, w, h, radius, color, fill=True):
        x,y,w,h,radius = int(x),int(y),int(w),int(h),int(radius)
        radius = min(radius, w//2, h//2)
        if fill:
            self.fill_rect(x+radius, y, w-2*radius, h, color)
            self.fill_rect(x, y+radius, radius, h-2*radius, color)
            self.fill_rect(x+w-radius, y+radius, radius, h-2*radius, color)
            corners = [(x+radius, y+radius), (x+w-radius-1, y+radius),
                       (x+radius, y+h-radius-1), (x+w-radius-1, y+h-radius-1)]
            for cx, cy in corners:
                self._fill_quarter(cx, cy, radius, color)
        else:
            self.line(x+radius, y, x+w-radius, y, color)
            self.line(x+radius, y+h-1, x+w-radius, y+h-1, color)
            self.line(x, y+radius, x, y+h-radius, color)
            self.line(x+w-1, y+radius, x+w-1, y+h-radius, color)

    def _fill_quarter(self, cx, cy, r, color):
        rc,gc,bc = _parse_color(color)
        for dy in range(-r, r+1):
            half = int((r*r - dy*dy) ** 0.5)
            for dx in range(-half, half+1):
                self._px(cx+dx, cy+dy, rc, gc, bc)


# ============================================================
# GUIイベント
# ============================================================
class GUIEvent:
    def __init__(self, etype, **kw):
        self.type = etype
        for k, v in kw.items():
            setattr(self, k, v)

    def __repr__(self):
        attrs = {k:v for k,v in self.__dict__.items() if k != "type"}
        return f"Event({self.type}, {attrs})"


# ============================================================
# Window (Win32直叩き)
# ============================================================
_CLASS_COUNTER = 0

class Window:
    def __init__(self, title, width, height):
        global _CLASS_COUNTER
        _CLASS_COUNTER += 1

        self.title = title
        self.width = width
        self.height = height
        self._open = True
        self._events = []
        self._mouse_x = 0
        self._mouse_y = 0
        self._keys = set()
        self._on_draw = None
        self._on_click = None
        self._on_key = None
        self._on_update = None
        self._fps = 60
        self._frame_count = 0
        self._start_time = time.perf_counter()

        self.canvas = Canvas(width, height)
        self.canvas.clear("white")

        self._class_name = f"SmileGUI_{_CLASS_COUNTER}"
        self._hwnd = None
        self._hdc = None
        self._mem_dc = None
        self._bitmap = None
        self._bits = None

        self._create_window()

    def _wndproc(self, hwnd, msg, wparam, lparam):
        if msg == WM_DESTROY:
            user32.PostQuitMessage(0)
            self._open = False
            return 0
        elif msg == WM_CLOSE:
            self._open = False
            user32.DestroyWindow(hwnd)
            return 0
        elif msg == WM_PAINT:
            self._blit()
            return user32.DefWindowProcW(hwnd, msg, wparam, lparam)
        elif msg == WM_ERASEBKGND:
            return 1
        elif msg == WM_SIZE:
            w = lparam & 0xFFFF
            h = (lparam >> 16) & 0xFFFF
            if w > 0 and h > 0:
                self.width = w
                self.height = h
                self.canvas.resize(w, h)
                self.canvas.clear("white")
                self._create_dib()
                self._events.append(GUIEvent("resize", width=w, height=h))
        elif msg == WM_LBUTTONDOWN:
            x = lparam & 0xFFFF
            y = (lparam >> 16) & 0xFFFF
            if x > 32767: x -= 65536
            if y > 32767: y -= 65536
            self._events.append(GUIEvent("click", x=x, y=y, button="left"))
        elif msg == WM_RBUTTONDOWN:
            x = lparam & 0xFFFF
            y = (lparam >> 16) & 0xFFFF
            if x > 32767: x -= 65536
            if y > 32767: y -= 65536
            self._events.append(GUIEvent("click", x=x, y=y, button="right"))
        elif msg == WM_LBUTTONUP:
            x = lparam & 0xFFFF
            y = (lparam >> 16) & 0xFFFF
            if x > 32767: x -= 65536
            if y > 32767: y -= 65536
            self._events.append(GUIEvent("release", x=x, y=y, button="left"))
        elif msg == WM_MOUSEMOVE:
            x = lparam & 0xFFFF
            y = (lparam >> 16) & 0xFFFF
            if x > 32767: x -= 65536
            if y > 32767: y -= 65536
            self._mouse_x = x
            self._mouse_y = y
            self._events.append(GUIEvent("move", x=x, y=y))
        elif msg == WM_MOUSEWHEEL:
            delta = ctypes.c_short((wparam >> 16) & 0xFFFF).value
            self._events.append(GUIEvent("wheel", delta=delta // 120))
        elif msg == WM_KEYDOWN:
            key = VK_MAP.get(wparam, chr(wparam).lower() if 32 <= wparam < 127 else f"vk{wparam}")
            self._keys.add(key)
            self._events.append(GUIEvent("keydown", key=key, vk=wparam))
        elif msg == WM_KEYUP:
            key = VK_MAP.get(wparam, chr(wparam).lower() if 32 <= wparam < 127 else f"vk{wparam}")
            self._keys.discard(key)
            self._events.append(GUIEvent("keyup", key=key, vk=wparam))
        elif msg == WM_CHAR:
            ch = chr(wparam) if wparam >= 32 else ""
            if ch:
                self._events.append(GUIEvent("char", char=ch))
        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def _create_window(self):
        hInstance = kernel32.GetModuleHandleW(None)
        self._wndproc_ref = WNDPROC(self._wndproc)

        wc = WNDCLASSEXW()
        wc.cbSize = ctypes.sizeof(WNDCLASSEXW)
        wc.style = CS_HREDRAW | CS_VREDRAW | CS_OWNDC
        wc.lpfnWndProc = self._wndproc_ref
        wc.hInstance = hInstance
        wc.hCursor = user32.LoadCursorW(None, ctypes.c_wchar_p(IDC_ARROW))
        wc.lpszClassName = self._class_name

        user32.RegisterClassExW(ctypes.byref(wc))

        rect = wt.RECT(0, 0, self.width, self.height)
        user32.AdjustWindowRect(ctypes.byref(rect), WS_OVERLAPPEDWINDOW, False)
        aw = rect.right - rect.left
        ah = rect.bottom - rect.top

        self._hwnd = user32.CreateWindowExW(
            0, self._class_name, self.title,
            WS_OVERLAPPEDWINDOW | WS_CLIPCHILDREN,
            CW_USEDEFAULT, CW_USEDEFAULT, aw, ah,
            None, None, hInstance, None,
        )

        self._hdc = user32.GetDC(self._hwnd)
        self._create_dib()

    def _create_dib(self):
        if self._mem_dc:
            gdi32.DeleteDC(self._mem_dc)
        if self._bitmap:
            gdi32.DeleteObject(self._bitmap)

        self._mem_dc = gdi32.CreateCompatibleDC(self._hdc)
        bmi = BITMAPINFO()
        bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.bmiHeader.biWidth = self.width
        bmi.bmiHeader.biHeight = -self.height
        bmi.bmiHeader.biPlanes = 1
        bmi.bmiHeader.biBitCount = 32
        bmi.bmiHeader.biCompression = 0

        self._bits = ctypes.c_void_p()
        self._bitmap = gdi32.CreateDIBSection(
            self._mem_dc, ctypes.byref(bmi), DIB_RGB_COLORS,
            ctypes.byref(self._bits), None, 0,
        )
        gdi32.SelectObject(self._mem_dc, self._bitmap)

    def _blit(self):
        if self._bits and self.canvas.buf:
            buf_bytes = bytes(self.canvas.buf)
            ctypes.memmove(self._bits, buf_bytes, len(buf_bytes))
            gdi32.BitBlt(self._hdc, 0, 0, self.width, self.height,
                         self._mem_dc, 0, 0, SRCCOPY)

    # ── 公開API ──

    def show(self):
        user32.ShowWindow(self._hwnd, 1)
        user32.UpdateWindow(self._hwnd)

    def hide(self):
        user32.ShowWindow(self._hwnd, 0)

    def close(self):
        self._open = False
        user32.DestroyWindow(self._hwnd)

    def is_open(self):
        return self._open

    def poll(self):
        msg = wt.MSG()
        while user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, PM_REMOVE):
            if msg.message == WM_QUIT:
                self._open = False
                return GUIEvent("quit")
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
        if self._events:
            return self._events.pop(0)
        return None

    def update(self):
        self._blit()
        self._frame_count += 1

    def wait(self, ms=16):
        time.sleep(ms / 1000.0)

    # ── 描画 (Canvasへの委譲) ──

    def fill(self, color="white"):
        self.canvas.clear(color)

    def rect(self, x, y, w, h, color, fill=True):
        if fill:
            self.canvas.fill_rect(x, y, w, h, color)
        else:
            self.canvas.stroke_rect(x, y, w, h, color)

    def rounded_rect(self, x, y, w, h, radius, color, fill=True):
        self.canvas.rounded_rect(x, y, w, h, radius, color, fill)

    def circle(self, cx, cy, r, color, fill=True):
        self.canvas.circle(cx, cy, r, color, fill)

    def line(self, x0, y0, x1, y1, color, thickness=1):
        self.canvas.line(x0, y0, x1, y1, color, thickness)

    def triangle(self, x0, y0, x1, y1, x2, y2, color, fill=True):
        self.canvas.triangle(x0, y0, x1, y1, x2, y2, color, fill)

    def gradient(self, x, y, w, h, c1, c2, vertical=True):
        self.canvas.gradient_rect(x, y, w, h, c1, c2, vertical)

    def pixel(self, x, y, color):
        r, g, b = _parse_color(color)
        self.canvas._px(int(x), int(y), r, g, b)

    def text(self, x, y, s, color="black", size=16, font="Yu Gothic UI", bold=False):
        weight = 700 if bold else 400
        hFont = gdi32.CreateFontW(
            -size, 0, 0, 0, weight, 0, 0, 0, 1, 0, 0, 4, 0, font,
        )
        old_font = gdi32.SelectObject(self._mem_dc, hFont)
        gdi32.SetTextColor(self._mem_dc, _colorref(color))
        gdi32.SetBkMode(self._mem_dc, TRANSPARENT)

        buf_bytes = bytes(self.canvas.buf)
        ctypes.memmove(self._bits, buf_bytes, len(buf_bytes))
        text_w = ctypes.create_unicode_buffer(str(s))
        rc = wt.RECT(int(x), int(y), self.width, self.height)
        user32.DrawTextW(self._mem_dc, text_w, -1, ctypes.byref(rc), DT_LEFT)
        buf_type = (ctypes.c_char * len(self.canvas.buf))
        ctypes.memmove(buf_type.from_buffer(self.canvas.buf), self._bits, len(self.canvas.buf))

        gdi32.SelectObject(self._mem_dc, old_font)
        gdi32.DeleteObject(hFont)
        self.canvas._dirty = True

    # ── 状態クエリ ──

    def mouse_x(self):
        return self._mouse_x

    def mouse_y(self):
        return self._mouse_y

    def key_pressed(self, key):
        return key.lower() in self._keys

    def fps(self):
        elapsed = time.perf_counter() - self._start_time
        if elapsed > 0:
            return self._frame_count / elapsed
        return 0

    def frame_count(self):
        return self._frame_count

    def set_title(self, title):
        self.title = title
        user32.SetWindowTextW(self._hwnd, title)

    def __repr__(self):
        return f"Window('{self.title}', {self.width}x{self.height}, open={self._open})"


# ============================================================
# 公開関数
# ============================================================

def window(title="Smile", width=800, height=600):
    """GUIウィンドウを作成"""
    return Window(title, width, height)

def gui_run(title, width, height, draw_fn, fps=60):
    """描画ループを自動実行"""
    win = Window(title, width, height)
    win.show()
    frame_time = 1.0 / fps
    while win.is_open():
        t0 = time.perf_counter()
        ev = win.poll()
        while ev is not None:
            ev = win.poll()
        draw_fn(win)
        win.update()
        dt = time.perf_counter() - t0
        if dt < frame_time:
            time.sleep(frame_time - dt)
    return win


# ============================================================
# UIウィジェット
# ============================================================
class Button:
    def __init__(self, x, y, w, h, label, color="#3366cc", text_color="white", font_size=14):
        self.x, self.y, self.w, self.h = int(x), int(y), int(w), int(h)
        self.label = label
        self.color = color
        self.text_color = text_color
        self.font_size = font_size
        self.hover = False
        self.pressed = False
        self._clicked = False

    def update(self, win):
        mx, my = win.mouse_x(), win.mouse_y()
        self.hover = self.x <= mx < self.x + self.w and self.y <= my < self.y + self.h
        self._clicked = False

    def handle(self, ev):
        if ev and ev.type == "click" and hasattr(ev, "x"):
            if self.x <= ev.x < self.x + self.w and self.y <= ev.y < self.y + self.h:
                self._clicked = True
                self.pressed = True
        if ev and ev.type == "release":
            self.pressed = False

    def clicked(self):
        c = self._clicked
        self._clicked = False
        return c

    def draw(self, win):
        r, g, b = _parse_color(self.color)
        if self.pressed:
            c = (max(0,r-40), max(0,g-40), max(0,b-40))
        elif self.hover:
            c = (min(255,r+30), min(255,g+30), min(255,b+30))
        else:
            c = (r, g, b)
        win.rounded_rect(self.x, self.y, self.w, self.h, 4, c)
        tx = self.x + self.w // 2 - len(self.label) * self.font_size // 4
        ty = self.y + (self.h - self.font_size) // 2
        win.text(tx, ty, self.label, color=self.text_color, size=self.font_size)


class Slider:
    def __init__(self, x, y, w, min_val=0, max_val=100, value=50, color="#3366cc"):
        self.x, self.y, self.w = int(x), int(y), int(w)
        self.min_val = min_val
        self.max_val = max_val
        self.value = value
        self.color = color
        self.dragging = False
        self.h = 20
        self._changed = False

    def handle(self, ev):
        if ev and ev.type == "click" and hasattr(ev, "x"):
            if self.x <= ev.x < self.x + self.w and self.y - 5 <= ev.y < self.y + self.h + 5:
                self.dragging = True
                self._set_from_x(ev.x)
        if ev and ev.type == "release":
            self.dragging = False
        if ev and ev.type == "move" and self.dragging and hasattr(ev, "x"):
            self._set_from_x(ev.x)

    def _set_from_x(self, mx):
        t = max(0.0, min(1.0, (mx - self.x) / self.w))
        new_val = self.min_val + t * (self.max_val - self.min_val)
        if new_val != self.value:
            self._changed = True
        self.value = new_val

    def changed(self):
        c = self._changed
        self._changed = False
        return c

    def draw(self, win):
        win.rounded_rect(self.x, self.y + 7, self.w, 6, 3, "darkgray")
        t = (self.value - self.min_val) / max(1, self.max_val - self.min_val)
        fill_w = int(self.w * t)
        if fill_w > 0:
            win.rounded_rect(self.x, self.y + 7, fill_w, 6, 3, self.color)
        knob_x = self.x + fill_w
        win.circle(knob_x, self.y + 10, 8, self.color)
        win.circle(knob_x, self.y + 10, 5, "white")


class TextInput:
    def __init__(self, x, y, w, h=28, placeholder="", font_size=14):
        self.x, self.y, self.w, self.h = int(x), int(y), int(w), int(h)
        self.text = ""
        self.placeholder = placeholder
        self.font_size = font_size
        self.focused = False
        self.cursor_pos = 0
        self._blink = 0

    def handle(self, ev):
        if ev and ev.type == "click" and hasattr(ev, "x"):
            self.focused = self.x <= ev.x < self.x + self.w and self.y <= ev.y < self.y + self.h
        if not self.focused:
            return
        if ev and ev.type == "char":
            self.text = self.text[:self.cursor_pos] + ev.char + self.text[self.cursor_pos:]
            self.cursor_pos += 1
        if ev and ev.type == "keydown":
            if ev.key == "backspace" and self.cursor_pos > 0:
                self.text = self.text[:self.cursor_pos-1] + self.text[self.cursor_pos:]
                self.cursor_pos -= 1
            elif ev.key == "delete" and self.cursor_pos < len(self.text):
                self.text = self.text[:self.cursor_pos] + self.text[self.cursor_pos+1:]
            elif ev.key == "left" and self.cursor_pos > 0:
                self.cursor_pos -= 1
            elif ev.key == "right" and self.cursor_pos < len(self.text):
                self.cursor_pos += 1
            elif ev.key == "home":
                self.cursor_pos = 0
            elif ev.key == "end":
                self.cursor_pos = len(self.text)

    def draw(self, win):
        self._blink += 1
        border = "#3366cc" if self.focused else "#888888"
        win.rounded_rect(self.x, self.y, self.w, self.h, 3, "white")
        win.canvas.stroke_rect(self.x, self.y, self.w, self.h, border, 2)
        if self.text:
            win.text(self.x + 4, self.y + (self.h - self.font_size) // 2,
                     self.text, color="black", size=self.font_size)
        elif self.placeholder:
            win.text(self.x + 4, self.y + (self.h - self.font_size) // 2,
                     self.placeholder, color="gray", size=self.font_size)
        if self.focused and (self._blink // 30) % 2 == 0:
            cx = self.x + 4 + self.cursor_pos * (self.font_size * 0.55)
            win.line(int(cx), self.y + 4, int(cx), self.y + self.h - 4, "black", 1)


class Checkbox:
    def __init__(self, x, y, label="", checked=False, size=18, color="#3366cc"):
        self.x, self.y = int(x), int(y)
        self.label = label
        self.checked = checked
        self.size = size
        self.color = color
        self._toggled = False

    def handle(self, ev):
        if ev and ev.type == "click" and hasattr(ev, "x"):
            if self.x <= ev.x < self.x + self.size + len(self.label) * 8 + 8 and \
               self.y <= ev.y < self.y + self.size:
                self.checked = not self.checked
                self._toggled = True

    def toggled(self):
        t = self._toggled
        self._toggled = False
        return t

    def draw(self, win):
        win.rounded_rect(self.x, self.y, self.size, self.size, 3, "white")
        win.canvas.stroke_rect(self.x, self.y, self.size, self.size, "#888888", 2)
        if self.checked:
            win.rounded_rect(self.x + 3, self.y + 3, self.size - 6, self.size - 6, 2, self.color)
        if self.label:
            win.text(self.x + self.size + 6, self.y + 1, self.label, color="black", size=self.size - 4)


# ============================================================
# 画像読み込み (BMP)
# ============================================================
def load_image(filepath):
    """BMPファイルを読み込んでCanvasに変換"""
    with open(filepath, "rb") as f:
        data = f.read()
    if data[:2] != b"BM":
        raise ValueError("BMPファイルではありません")
    offset = struct.unpack_from("<I", data, 10)[0]
    w = struct.unpack_from("<i", data, 18)[0]
    h = struct.unpack_from("<i", data, 22)[0]
    bpp = struct.unpack_from("<H", data, 28)[0]
    flip = h > 0
    h = abs(h)
    canvas = Canvas(w, h)
    if bpp == 24:
        row_size = (w * 3 + 3) & ~3
        for y in range(h):
            src_y = (h - 1 - y) if flip else y
            for x in range(w):
                idx = offset + src_y * row_size + x * 3
                b, g, r = data[idx], data[idx+1], data[idx+2]
                canvas._px(x, y, r, g, b)
    elif bpp == 32:
        row_size = w * 4
        for y in range(h):
            src_y = (h - 1 - y) if flip else y
            for x in range(w):
                idx = offset + src_y * row_size + x * 4
                b, g, r, a = data[idx], data[idx+1], data[idx+2], data[idx+3]
                canvas._px(x, y, r, g, b, a)
    return canvas


def save_bmp(canvas, filepath):
    """CanvasをBMPファイルに保存"""
    w, h = canvas.w, canvas.h
    row_size = (w * 3 + 3) & ~3
    img_size = row_size * h
    file_size = 54 + img_size
    header = struct.pack("<2sIHHI", b"BM", file_size, 0, 0, 54)
    info = struct.pack("<IiiHHIIiiII", 40, w, h, 1, 24, 0, img_size, 0, 0, 0, 0)
    with open(filepath, "wb") as f:
        f.write(header)
        f.write(info)
        for y in range(h - 1, -1, -1):
            row = bytearray()
            for x in range(w):
                off = (y * w + x) * 4
                row.append(canvas.buf[off])      # B
                row.append(canvas.buf[off + 1])   # G
                row.append(canvas.buf[off + 2])   # R
            row.extend(b"\x00" * (row_size - w * 3))
            f.write(row)


# ============================================================
# 音声 (Win32)
# ============================================================
_winmm = None
def _get_winmm():
    global _winmm
    if _winmm is None:
        _winmm = ctypes.windll.winmm
    return _winmm

SND_FILENAME = 0x00020000
SND_ASYNC = 0x0001
SND_SYNC = 0x0000

def play_sound(filepath, sync=False):
    """WAVファイルを再生"""
    winmm = _get_winmm()
    flags = SND_FILENAME | (SND_SYNC if sync else SND_ASYNC)
    winmm.PlaySoundW(filepath, None, flags)

def stop_sound():
    """音声再生を停止"""
    winmm = _get_winmm()
    winmm.PlaySoundW(None, None, 0)

def beep(freq=440, duration=200):
    """ビープ音を鳴らす (周波数Hz, 時間ms)"""
    kernel32.Beep(int(freq), int(duration))
