"""Smile 低レイヤーライブラリ - 安全にハードウェアやメモリを操作

BIOSやポートI/O、メモリ直接操作、バイナリ操作を
安全なSmile関数でラップ。範囲チェック・型チェック付き。
"""

import sys
import os
import struct
import ctypes
import mmap

_is_windows = sys.platform == "win32"

# ============================================================
# バイナリ操作 (安全・どこでも動く)
# ============================================================

def bytes_new(size, fill=0):
    """指定サイズのバイト列を作成"""
    if size < 0 or size > 1024 * 1024 * 1024:
        raise ValueError(f"サイズが不正です: {size} (0〜1GBまで)")
    return bytearray([fill & 0xFF] * size)

def bytes_from(data):
    """リストやint列からバイト列を作成"""
    if isinstance(data, str):
        return bytearray(data.encode("utf-8"))
    return bytearray(data)

def bytes_read(buf, offset, size):
    """バイト列から指定範囲を読む"""
    if offset < 0 or offset + size > len(buf):
        raise IndexError(f"範囲外アクセス: offset={offset}, size={size}, バッファ長={len(buf)}")
    return bytes(buf[offset:offset + size])

def bytes_write(buf, offset, data):
    """バイト列に書き込み"""
    if isinstance(data, int):
        data = [data & 0xFF]
    if offset < 0 or offset + len(data) > len(buf):
        raise IndexError(f"範囲外書き込み: offset={offset}, data長={len(data)}, バッファ長={len(buf)}")
    buf[offset:offset + len(data)] = data
    return buf

def bytes_to_hex(buf):
    """バイト列を16進数文字列に変換"""
    return bytes(buf).hex()

def bytes_from_hex(hex_str):
    """16進数文字列からバイト列を作成"""
    return bytearray(bytes.fromhex(hex_str.replace(" ", "").replace("0x", "")))

def bytes_to_list(buf):
    """バイト列をint型リストに変換"""
    return list(buf)

def bytes_dump(buf, cols=16):
    """バイト列をhexdump表示"""
    lines = []
    for i in range(0, len(buf), cols):
        row = buf[i:i + cols]
        hex_part = " ".join(f"{b:02X}" for b in row)
        ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in row)
        lines.append(f"  {i:08X}  {hex_part:<{cols*3}}  |{ascii_part}|")
    return "\n".join(lines)

# ============================================================
# パック/アンパック (構造体的なバイナリ操作)
# ============================================================

def pack_u8(value):
    return struct.pack("B", value & 0xFF)

def pack_u16(value, little=True):
    return struct.pack("<H" if little else ">H", value & 0xFFFF)

def pack_u32(value, little=True):
    return struct.pack("<I" if little else ">I", value & 0xFFFFFFFF)

def pack_u64(value, little=True):
    return struct.pack("<Q" if little else ">Q", value & 0xFFFFFFFFFFFFFFFF)

def pack_i8(value):
    return struct.pack("b", value)

def pack_i16(value, little=True):
    return struct.pack("<h" if little else ">h", value)

def pack_i32(value, little=True):
    return struct.pack("<i" if little else ">i", value)

def pack_i64(value, little=True):
    return struct.pack("<q" if little else ">q", value)

def pack_f32(value, little=True):
    return struct.pack("<f" if little else ">f", value)

def pack_f64(value, little=True):
    return struct.pack("<d" if little else ">d", value)

def unpack_u8(data, offset=0):
    return struct.unpack_from("B", data, offset)[0]

def unpack_u16(data, offset=0, little=True):
    return struct.unpack_from("<H" if little else ">H", data, offset)[0]

def unpack_u32(data, offset=0, little=True):
    return struct.unpack_from("<I" if little else ">I", data, offset)[0]

def unpack_u64(data, offset=0, little=True):
    return struct.unpack_from("<Q" if little else ">Q", data, offset)[0]

def unpack_i8(data, offset=0):
    return struct.unpack_from("b", data, offset)[0]

def unpack_i16(data, offset=0, little=True):
    return struct.unpack_from("<h" if little else ">h", data, offset)[0]

def unpack_i32(data, offset=0, little=True):
    return struct.unpack_from("<i" if little else ">i", data, offset)[0]

def unpack_i64(data, offset=0, little=True):
    return struct.unpack_from("<q" if little else ">q", data, offset)[0]

def unpack_f32(data, offset=0, little=True):
    return struct.unpack_from("<f" if little else ">f", data, offset)[0]

def unpack_f64(data, offset=0, little=True):
    return struct.unpack_from("<d" if little else ">d", data, offset)[0]

# ============================================================
# ビット操作
# ============================================================

def bit_and(a, b):
    return a & b

def bit_or(a, b):
    return a | b

def bit_xor(a, b):
    return a ^ b

def bit_not(a, bits=32):
    """ビット反転 (指定ビット幅)"""
    mask = (1 << bits) - 1
    return (~a) & mask

def bit_shift_left(a, n):
    return a << n

def bit_shift_right(a, n):
    return a >> n

def bit_get(value, bit):
    """特定ビットの値を取得 (0 or 1)"""
    return (value >> bit) & 1

def bit_set(value, bit):
    """特定ビットを1にセット"""
    return value | (1 << bit)

def bit_clear(value, bit):
    """特定ビットを0にクリア"""
    return value & ~(1 << bit)

def bit_toggle(value, bit):
    """特定ビットを反転"""
    return value ^ (1 << bit)

def bit_count(value):
    """1のビット数を数える"""
    return bin(value).count("1")

def to_bin(value, bits=None):
    """2進数文字列に変換"""
    if bits:
        return format(value & ((1 << bits) - 1), f"0{bits}b")
    return bin(value)

def to_hex(value, width=0):
    """16進数文字列に変換"""
    if width:
        return format(value, f"0{width}x")
    return hex(value)

def to_oct(value):
    """8進数文字列に変換"""
    return oct(value)

def from_bin(s):
    """2進数文字列から整数に変換"""
    return int(s.replace("0b", ""), 2)

def from_hex(s):
    """16進数文字列から整数に変換"""
    return int(s.replace("0x", ""), 16)

# ============================================================
# メモリマップドI/O (安全ラッパー)
# ============================================================

class MemoryRegion:
    """メモリ領域を安全にラップ"""
    def __init__(self, data, base_addr=0, label="memory"):
        self._data = bytearray(data) if not isinstance(data, (bytearray, mmap.mmap)) else data
        self._base = base_addr
        self._label = label

    def __len__(self):
        return len(self._data)

    def __repr__(self):
        return f"MemoryRegion({self._label}, base=0x{self._base:X}, size={len(self._data)})"

    def _check(self, offset, size):
        if offset < 0 or offset + size > len(self._data):
            raise IndexError(
                f"メモリアクセス違反: {self._label} の "
                f"0x{self._base + offset:X} (offset={offset}, size={size}) は範囲外です。"
                f"\n  有効範囲: 0x{self._base:X}〜0x{self._base + len(self._data) - 1:X} "
                f"({len(self._data)} バイト)"
            )

    def read_u8(self, offset):
        self._check(offset, 1)
        return self._data[offset]

    def read_u16(self, offset, little=True):
        self._check(offset, 2)
        return struct.unpack_from("<H" if little else ">H", self._data, offset)[0]

    def read_u32(self, offset, little=True):
        self._check(offset, 4)
        return struct.unpack_from("<I" if little else ">I", self._data, offset)[0]

    def read_u64(self, offset, little=True):
        self._check(offset, 8)
        return struct.unpack_from("<Q" if little else ">Q", self._data, offset)[0]

    def read_bytes(self, offset, size):
        self._check(offset, size)
        return bytes(self._data[offset:offset + size])

    def read_string(self, offset, max_len=256):
        """NULL終端文字列を読む"""
        self._check(offset, 1)
        end = offset
        while end < min(offset + max_len, len(self._data)) and self._data[end] != 0:
            end += 1
        return bytes(self._data[offset:end]).decode("utf-8", errors="replace")

    def write_u8(self, offset, value):
        self._check(offset, 1)
        self._data[offset] = value & 0xFF

    def write_u16(self, offset, value, little=True):
        self._check(offset, 2)
        struct.pack_into("<H" if little else ">H", self._data, offset, value & 0xFFFF)

    def write_u32(self, offset, value, little=True):
        self._check(offset, 4)
        struct.pack_into("<I" if little else ">I", self._data, offset, value & 0xFFFFFFFF)

    def write_u64(self, offset, value, little=True):
        self._check(offset, 8)
        struct.pack_into("<Q" if little else ">Q", self._data, offset, value & 0xFFFFFFFFFFFFFFFF)

    def write_bytes(self, offset, data):
        self._check(offset, len(data))
        self._data[offset:offset + len(data)] = data

    def write_string(self, offset, s):
        """NULL終端文字列を書き込む"""
        encoded = s.encode("utf-8") + b"\x00"
        self._check(offset, len(encoded))
        self._data[offset:offset + len(encoded)] = encoded

    def fill(self, value, offset=0, size=None):
        if size is None:
            size = len(self._data) - offset
        self._check(offset, size)
        for i in range(offset, offset + size):
            self._data[i] = value & 0xFF

    def dump(self, offset=0, size=None, cols=16):
        if size is None:
            size = min(256, len(self._data) - offset)
        self._check(offset, size)
        lines = [f"  {self._label} @ 0x{self._base:X} (offset 0x{offset:X}, {size} bytes):"]
        for i in range(offset, offset + size, cols):
            row = self._data[i:min(i + cols, offset + size)]
            addr = self._base + i
            hex_part = " ".join(f"{b:02X}" for b in row)
            ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in row)
            lines.append(f"  {addr:08X}  {hex_part:<{cols * 3}}  |{ascii_part}|")
        return "\n".join(lines)

    def to_bytes(self):
        return bytes(self._data)

    def slice(self, offset, size, label=None):
        """サブ領域を取得（コピー）"""
        self._check(offset, size)
        return MemoryRegion(
            self._data[offset:offset + size],
            self._base + offset,
            label or f"{self._label}+0x{offset:X}"
        )

    def find_bytes(self, pattern, start=0):
        """バイトパターンを検索"""
        if isinstance(pattern, list):
            pattern = bytes(pattern)
        idx = bytes(self._data).find(pattern, start)
        return idx if idx >= 0 else -1


def memory_new(size, base_addr=0, label="memory"):
    """新しいメモリ領域を確保"""
    return MemoryRegion(bytearray(size), base_addr, label)

def memory_from(data, base_addr=0, label="memory"):
    """データからメモリ領域を作成"""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return MemoryRegion(bytearray(data), base_addr, label)

def memory_load(path, base_addr=0, label=None):
    """ファイルからメモリ領域にロード"""
    with open(path, "rb") as f:
        data = f.read()
    return MemoryRegion(bytearray(data), base_addr, label or os.path.basename(path))

def memory_save(region, path):
    """メモリ領域をファイルに保存"""
    with open(path, "wb") as f:
        f.write(region.to_bytes())


# ============================================================
# ポートI/O (Windows: WinRing0ベース, 管理者権限必要)
# ============================================================

class PortIO:
    """ポートI/Oの安全ラッパー (仮想/実ハードウェア対応)"""
    def __init__(self):
        self._log = []
        self._virtual = {}
        self._real = False

    def enable_real(self):
        """実ハードウェアポートI/Oを有効化 (管理者権限必要)"""
        if not _is_windows:
            raise RuntimeError("実ポートI/OはWindowsのみ対応です")
        self._real = True
        print("[PortIO] 実ハードウェアモード有効 (管理者権限が必要です)")

    def _log_access(self, op, port, value, size):
        self._log.append({"op": op, "port": port, "value": value, "size": size})

    def read_u8(self, port):
        """8ビット ポート読み出し"""
        if port in self._virtual:
            val = self._virtual[port] & 0xFF
        elif self._real:
            val = self._real_inb(port)
        else:
            val = 0xFF
        self._log_access("IN", port, val, 1)
        return val

    def read_u16(self, port):
        """16ビット ポート読み出し"""
        lo = self.read_u8(port)
        hi = self.read_u8(port + 1)
        return lo | (hi << 8)

    def write_u8(self, port, value):
        """8ビット ポート書き込み"""
        value &= 0xFF
        self._virtual[port] = value
        self._log_access("OUT", port, value, 1)

    def write_u16(self, port, value):
        """16ビット ポート書き込み"""
        self.write_u8(port, value & 0xFF)
        self.write_u8(port + 1, (value >> 8) & 0xFF)

    def set_virtual(self, port, value):
        """仮想ポートに値をセット (テスト用)"""
        self._virtual[port] = value & 0xFF

    def get_log(self):
        """アクセスログを取得"""
        return self._log

    def clear_log(self):
        self._log = []

    def dump_log(self):
        """アクセスログを表示"""
        lines = ["  Port I/O Log:"]
        for entry in self._log:
            op = entry["op"]
            port = entry["port"]
            val = entry["value"]
            lines.append(f"    {op}  port=0x{port:04X}  value=0x{val:02X} ({val})")
        return "\n".join(lines)

    def _real_inb(self, port):
        """ctypes経由で実ポート読み出し (Windowsのみ、WinRing0不要版)"""
        try:
            msvcrt = ctypes.cdll.msvcrt
            return msvcrt._inp(port) & 0xFF
        except Exception:
            return 0xFF


def port_io_new():
    """PortIOインスタンスを作成"""
    return PortIO()


# ============================================================
# BIOS/UEFI テーブル (安全な読み取り専用アクセス)
# ============================================================

def bios_read_smbios():
    """SMBIOSテーブルを読み取り (Windows)"""
    if not _is_windows:
        return {"error": "WindowsのみSMBIOS読み取りに対応しています"}

    try:
        kernel32 = ctypes.windll.kernel32

        size = kernel32.GetSystemFirmwareTable(
            0x52534D42,  # 'RSMB'
            0, None, 0
        )
        if size == 0:
            return {"error": "SMBIOSテーブルが取得できません (管理者権限が必要かもしれません)"}

        buf = ctypes.create_string_buffer(size)
        kernel32.GetSystemFirmwareTable(0x52534D42, 0, buf, size)
        raw = bytearray(buf.raw)

        result = {
            "raw_size": size,
            "tables": []
        }

        offset = 8
        while offset < len(raw) - 4:
            ttype = raw[offset]
            tlen = raw[offset + 1]
            thandle = raw[offset + 2] | (raw[offset + 3] << 8)

            if tlen < 4:
                break

            table_data = raw[offset:offset + tlen]

            strings = []
            str_offset = offset + tlen
            if str_offset < len(raw) and raw[str_offset] == 0:
                str_offset += 1
            else:
                while str_offset < len(raw) - 1:
                    if raw[str_offset] == 0:
                        str_offset += 1
                        break
                    end = str_offset
                    while end < len(raw) and raw[end] != 0:
                        end += 1
                    strings.append(raw[str_offset:end].decode("latin-1", errors="replace"))
                    str_offset = end + 1

            name = _smbios_type_name(ttype)
            result["tables"].append({
                "type": ttype,
                "name": name,
                "handle": thandle,
                "length": tlen,
                "data": bytes(table_data),
                "strings": strings,
            })

            offset = str_offset

        return result

    except Exception as e:
        return {"error": f"SMBIOSの読み取りに失敗: {e}"}


def _smbios_type_name(t):
    names = {
        0: "BIOS Information",
        1: "System Information",
        2: "Baseboard Information",
        3: "Chassis Information",
        4: "Processor Information",
        7: "Cache Information",
        9: "System Slots",
        16: "Physical Memory Array",
        17: "Memory Device",
        19: "Memory Array Mapped Address",
        32: "System Boot Information",
    }
    return names.get(t, f"Type {t}")


def bios_info():
    """BIOS情報を取得 (メーカー、バージョンなど)"""
    smbios = bios_read_smbios()
    if "error" in smbios:
        return smbios

    for table in smbios.get("tables", []):
        if table["type"] == 0 and table["strings"]:
            s = table["strings"]
            return {
                "vendor": s[0] if len(s) > 0 else "?",
                "version": s[1] if len(s) > 1 else "?",
                "release_date": s[2] if len(s) > 2 else "?",
            }
    return {"error": "BIOS情報が見つかりません"}


def system_info():
    """システム情報を取得 (メーカー、モデルなど)"""
    smbios = bios_read_smbios()
    if "error" in smbios:
        return smbios

    for table in smbios.get("tables", []):
        if table["type"] == 1 and table["strings"]:
            s = table["strings"]
            return {
                "manufacturer": s[0] if len(s) > 0 else "?",
                "product": s[1] if len(s) > 1 else "?",
                "version": s[2] if len(s) > 2 else "?",
                "serial": s[3] if len(s) > 3 else "?",
            }
    return {"error": "システム情報が見つかりません"}


def cpu_info_smbios():
    """CPU情報をSMBIOSから取得"""
    smbios = bios_read_smbios()
    if "error" in smbios:
        return smbios

    cpus = []
    for table in smbios.get("tables", []):
        if table["type"] == 4 and table["strings"]:
            s = table["strings"]
            data = table["data"]
            cpus.append({
                "socket": s[0] if len(s) > 0 else "?",
                "name": s[2] if len(s) > 2 else "?",
                "manufacturer": s[1] if len(s) > 1 else "?",
                "max_speed_mhz": (data[0x16] | (data[0x17] << 8)) if len(data) > 0x17 else 0,
                "current_speed_mhz": (data[0x18] | (data[0x19] << 8)) if len(data) > 0x19 else 0,
            })
    return cpus


def memory_info_smbios():
    """メモリ情報をSMBIOSから取得"""
    smbios = bios_read_smbios()
    if "error" in smbios:
        return smbios

    devices = []
    for table in smbios.get("tables", []):
        if table["type"] == 17 and len(table["data"]) > 0x0D:
            s = table["strings"]
            data = table["data"]
            size_raw = data[0x0C] | (data[0x0D] << 8)
            if size_raw == 0 or size_raw == 0xFFFF:
                continue
            size_mb = size_raw & 0x7FFF
            if size_raw & 0x8000:
                size_mb_actual = size_mb  # KB単位
            else:
                size_mb_actual = size_mb  # MB単位
            devices.append({
                "size_mb": size_mb_actual,
                "manufacturer": s[0] if len(s) > 0 else "?",
                "serial": s[1] if len(s) > 1 else "?",
                "part_number": s[2] if len(s) > 2 else "?",
            })
    return devices


# ============================================================
# ACPI テーブル (Windows)
# ============================================================

def acpi_read_table(signature):
    """ACPIテーブルを読み取り (4文字のシグネチャ指定)"""
    if not _is_windows:
        return {"error": "WindowsのみACPI読み取りに対応しています"}

    try:
        sig_int = struct.unpack(">I", signature.encode("ascii")[:4])[0]
        kernel32 = ctypes.windll.kernel32

        size = kernel32.GetSystemFirmwareTable(
            0x41435049,  # 'ACPI'
            sig_int, None, 0
        )
        if size == 0:
            return {"error": f"ACPIテーブル '{signature}' が見つかりません"}

        buf = ctypes.create_string_buffer(size)
        kernel32.GetSystemFirmwareTable(0x41435049, sig_int, buf, size)

        raw = bytearray(buf.raw)
        return {
            "signature": signature,
            "size": size,
            "data": MemoryRegion(raw, 0, f"ACPI:{signature}"),
        }
    except Exception as e:
        return {"error": f"ACPIテーブルの読み取りに失敗: {e}"}


def acpi_list_tables():
    """利用可能なACPIテーブル一覧"""
    if not _is_windows:
        return {"error": "WindowsのみACPI対応"}

    try:
        kernel32 = ctypes.windll.kernel32
        size = kernel32.EnumSystemFirmwareTables(0x41435049, None, 0)
        if size == 0:
            return []
        buf = ctypes.create_string_buffer(size)
        kernel32.EnumSystemFirmwareTables(0x41435049, buf, size)
        raw = buf.raw[:size]
        tables = []
        for i in range(0, len(raw), 4):
            sig = raw[i:i+4].decode("ascii", errors="replace")
            tables.append(sig)
        return tables
    except Exception:
        return []


# ============================================================
# バイナリファイル操作
# ============================================================

def binary_read(path):
    """バイナリファイルを読み込み MemoryRegion として返す"""
    with open(path, "rb") as f:
        data = f.read()
    return MemoryRegion(bytearray(data), 0, os.path.basename(path))

def binary_write(path, data):
    """バイナリデータをファイルに書き込み"""
    if isinstance(data, MemoryRegion):
        data = data.to_bytes()
    elif isinstance(data, list):
        data = bytes(data)
    with open(path, "wb") as f:
        f.write(data)

def binary_patch(path, offset, data):
    """バイナリファイルの特定位置にパッチ適用"""
    if isinstance(data, list):
        data = bytes(data)
    with open(path, "r+b") as f:
        f.seek(offset)
        f.write(data)


# ============================================================
# MBR / ブートセクタ操作 (安全な仮想操作)
# ============================================================

def mbr_new():
    """空のMBR (512バイト) を作成"""
    mbr = memory_new(512, 0x7C00, "MBR")
    mbr.write_u16(510, 0xAA55)  # ブートシグネチャ
    return mbr

def mbr_set_partition(mbr, index, status, ptype, lba_start, sectors):
    """MBRパーティションテーブルエントリを設定"""
    if index < 0 or index > 3:
        raise ValueError("パーティションインデックスは0〜3です")
    offset = 446 + index * 16
    mbr.write_u8(offset, status & 0xFF)
    mbr.write_u8(offset + 1, 0)  # CHS start (unused)
    mbr.write_u8(offset + 2, 0)
    mbr.write_u8(offset + 3, 0)
    mbr.write_u8(offset + 4, ptype & 0xFF)
    mbr.write_u8(offset + 5, 0)  # CHS end (unused)
    mbr.write_u8(offset + 6, 0)
    mbr.write_u8(offset + 7, 0)
    mbr.write_u32(offset + 8, lba_start)
    mbr.write_u32(offset + 12, sectors)

def mbr_read_partition(mbr, index):
    """MBRパーティションテーブルエントリを読む"""
    if index < 0 or index > 3:
        raise ValueError("パーティションインデックスは0〜3です")
    offset = 446 + index * 16
    return {
        "status": mbr.read_u8(offset),
        "type": mbr.read_u8(offset + 4),
        "lba_start": mbr.read_u32(offset + 8),
        "sectors": mbr.read_u32(offset + 12),
        "bootable": mbr.read_u8(offset) == 0x80,
    }

def mbr_check_signature(mbr):
    """ブートシグネチャを検証"""
    sig = mbr.read_u16(510)
    return sig == 0xAA55


# ============================================================
# x86アセンブリ関連 (機械語生成ヘルパー)
# ============================================================

class AsmBuilder:
    """x86/x86-64 機械語を安全に組み立てるビルダー"""

    def __init__(self, bits=64, base=0):
        self._code = bytearray()
        self._bits = bits
        self._base = base
        self._labels = {}
        self._fixups = []

    def __len__(self):
        return len(self._code)

    def emit(self, *bytez):
        """バイト列を出力"""
        for b in bytez:
            if isinstance(b, (list, tuple, bytes, bytearray)):
                self._code.extend(b)
            else:
                self._code.append(b & 0xFF)

    def label(self, name):
        """ラベルを定義"""
        self._labels[name] = len(self._code)

    def current_offset(self):
        return len(self._code)

    # --- よく使うx86命令 ---
    def nop(self):
        self.emit(0x90)

    def ret(self):
        self.emit(0xC3)

    def hlt(self):
        self.emit(0xF4)

    def cli(self):
        self.emit(0xFA)

    def sti(self):
        self.emit(0xFB)

    def int_(self, n):
        """INT n"""
        self.emit(0xCD, n & 0xFF)

    def mov_al(self, imm8):
        self.emit(0xB0, imm8 & 0xFF)

    def mov_ah(self, imm8):
        self.emit(0xB4, imm8 & 0xFF)

    def mov_ax(self, imm16):
        self.emit(0xB8, imm16 & 0xFF, (imm16 >> 8) & 0xFF)

    def mov_eax(self, imm32):
        self.emit(0xB8)
        self.emit(pack_u32(imm32))

    def jmp_short(self, offset):
        """短い相対ジャンプ (-128〜+127)"""
        self.emit(0xEB, offset & 0xFF)

    def to_memory(self, base_addr=None):
        """MemoryRegionとして返す"""
        return MemoryRegion(
            bytearray(self._code),
            base_addr if base_addr is not None else self._base,
            "asm"
        )

    def to_bytes(self):
        return bytes(self._code)

    def dump(self):
        return bytes_dump(self._code)


def asm_new(bits=64, base=0):
    """アセンブラビルダーを作成"""
    return AsmBuilder(bits, base)


# ============================================================
# エクスポート
# ============================================================

def _get_all_exports():
    import types
    g = globals()
    return {name: obj for name, obj in g.items()
            if not name.startswith("_")
            and not isinstance(obj, types.ModuleType)}

EXPORTS = _get_all_exports()
