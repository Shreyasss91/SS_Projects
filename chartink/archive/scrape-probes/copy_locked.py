"""Copy a locked file using Windows CreateFile with share flags."""
from __future__ import annotations

import ctypes
import tempfile
from ctypes import wintypes
from pathlib import Path

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

GENERIC_READ = 0x80000000
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
FILE_SHARE_DELETE = 0x00000004
OPEN_EXISTING = 3
FILE_ATTRIBUTE_NORMAL = 0x80
INVALID_HANDLE_VALUE = wintypes.HANDLE(-1).value


def copy_locked_file(src: Path, dst: Path) -> None:
    handle = kernel32.CreateFileW(
        str(src),
        GENERIC_READ,
        FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
        None,
        OPEN_EXISTING,
        FILE_ATTRIBUTE_NORMAL,
        None,
    )
    if handle == INVALID_HANDLE_VALUE or handle == -1:
        err = ctypes.get_last_error()
        raise OSError(err, f"CreateFileW failed for {src}")

    chunks = []
    try:
        buf = ctypes.create_string_buffer(1024 * 1024)
        read = wintypes.DWORD(0)
        while True:
            ok = kernel32.ReadFile(handle, buf, len(buf), ctypes.byref(read), None)
            if not ok:
                err = ctypes.get_last_error()
                raise OSError(err, "ReadFile failed")
            if read.value == 0:
                break
            chunks.append(buf.raw[: read.value])
    finally:
        kernel32.CloseHandle(handle)

    dst.write_bytes(b"".join(chunks))
    print(f"copied {src} -> {dst} bytes={dst.stat().st_size}")


if __name__ == "__main__":
    src = (
        Path.home()
        / "AppData/Local/Google/Chrome/User Data/Default/Network/Cookies"
    )
    dst = Path(tempfile.mkdtemp()) / "Cookies"
    copy_locked_file(src, dst)
    print("ok", dst)
