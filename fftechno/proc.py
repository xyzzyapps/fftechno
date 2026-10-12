"""Process helpers: run commands with consistent, quiet ffmpeg defaults."""

from __future__ import annotations

import os
import subprocess
from collections.abc import Sequence
from contextlib import contextmanager, suppress
from pathlib import Path


@contextmanager
def build_lock(path: Path):
    """Exclusive lock so two builds cannot write the same outputs at once."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise SystemExit(
            f"another fftechno build is running ({path}); "
            "remove the file if it is stale"
        ) from exc
    try:
        os.write(fd, str(os.getpid()).encode())
        yield
    finally:
        os.close(fd)
        with suppress(OSError):
            os.remove(path)


def run(cmd: Sequence[object], *, log: Path | None = None, check: bool = True) -> int:
    """Run *cmd*. Redirect stderr to *log* (or suppress it); raise on failure."""
    args = [str(a) for a in cmd]
    if log is not None:
        log.parent.mkdir(parents=True, exist_ok=True)
        with open(log, "wb") as fh:
            code = subprocess.run(args, stdout=subprocess.DEVNULL, stderr=fh).returncode
    else:
        code = subprocess.run(
            args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        ).returncode
    if check and code != 0:
        raise SystemExit(f"command failed ({code}): {' '.join(args)}")
    return code


def ffmpeg(args: Sequence[object], *, log: Path | None = None) -> int:
    """Run ffmpeg with quiet defaults (``-v error``) and optional stderr log."""
    return run(["ffmpeg", "-hide_banner", "-nostdin", "-v", "error", *args], log=log)
