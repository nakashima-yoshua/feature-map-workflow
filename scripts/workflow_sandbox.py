#!/usr/bin/env python3
"""Landlock-restricted Build child; no unsafe fallback or extra container privilege.

ABI/constants: https://docs.kernel.org/userspace-api/landlock.html
The wrapper runs in a separate process; restrictions propagate to exec/descendants.
Docker supplies network/PID/mount isolation. Landlock hides worker results/requests
and permits writes only under this command's private temporary directory.
"""
from __future__ import annotations

import argparse
import ctypes
import os
import platform
import sys
from pathlib import Path

READ = (1 << 0) | (1 << 2) | (1 << 3)  # execute, read_file, read_dir
ALL = (1 << 15) - 1  # ABI 3: includes REFER and TRUNCATE
FILE = (1 << 0) | (1 << 1) | (1 << 2) | (1 << 14)


class Ruleset(ctypes.Structure):
    _fields_ = [("handled_access_fs", ctypes.c_uint64)]


class Beneath(ctypes.Structure):
    _pack_ = 1
    _fields_ = [("allowed_access", ctypes.c_uint64), ("parent_fd", ctypes.c_int32)]


def restrict(source: Path, temporary: Path) -> None:
    if platform.system() != "Linux" or platform.machine() not in {"x86_64", "aarch64"}:
        raise RuntimeError("Build isolation requires Linux x86_64/aarch64 and Landlock ABI >= 3")
    libc = ctypes.CDLL(None, use_errno=True)
    libc.syscall.restype = ctypes.c_long
    def call(number, *args):
        value = libc.syscall(number, *args)
        if value < 0:
            raise OSError(ctypes.get_errno(), "Landlock isolation unavailable; command was not executed")
        return value
    abi = call(444, None, 0, 1)
    if abi < 3:
        raise RuntimeError("Landlock ABI >= 3 is required; command was not executed")
    attr = Ruleset(ALL)
    ruleset = call(444, ctypes.byref(attr), ctypes.sizeof(attr), 0)
    try:
        grants = [(Path(p), READ) for p in ("/usr", "/bin", "/lib", "/lib64", "/etc", "/proc")]
        grants += [(source.resolve(), READ), (temporary.resolve(), ALL),
                   (Path("/dev/null"), (1 << 1) | (1 << 2)), (Path("/dev/urandom"), 1 << 2)]
        for path, access in grants:
            if not path.exists():
                continue
            fd = os.open(path, os.O_PATH | os.O_CLOEXEC)
            try:
                beneath = Beneath(access if path.is_dir() else access & FILE, fd)
                call(445, ruleset, 1, ctypes.byref(beneath), 0)
            finally:
                os.close(fd)
        if libc.prctl(38, 1, 0, 0, 0):  # PR_SET_NO_NEW_PRIVS
            raise OSError(ctypes.get_errno(), "Cannot enforce no-new-privileges")
        call(446, ruleset, 0)
    finally:
        os.close(ruleset)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--temporary", type=Path, required=True)
    parser.add_argument("argv", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    argv = args.argv[1:] if args.argv[:1] == ["--"] else args.argv
    if not argv:
        parser.error("an approved argv array is required")
    try:
        restrict(args.source, args.temporary)
        os.execvpe(argv[0], argv, os.environ)
    except (OSError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 125


if __name__ == "__main__":
    raise SystemExit(main())
