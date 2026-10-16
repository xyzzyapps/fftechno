"""Download + normalise the sample sets under ``samples/``.

``samples/manifest.md`` lists every sample (``set``/``file``/``url``/``license``).
``fetch`` downloads the missing ones; ``prepare`` transcodes each to a canonical
48 kHz PCM WAV, which also strips the malformed trailing packet some 24-bit sources
carry (that packet makes ffmpeg log ``Invalid PCM packet``).

    python -m fftechno samples           # fetch missing + normalise
    python -m fftechno samples --force   # re-download and re-normalise everything

The files themselves are not committed; the manifest is. This mirrors how the RVM
model and the Piper/Kitten voices live under ``tools/``.
"""

from __future__ import annotations

import json
import subprocess
import urllib.request
from pathlib import Path

from . import config as C
from .md import rows
from .proc import build_lock, ffmpeg

MANIFEST = C.ROOT / "samples" / "manifest.md"
SAMPLES = C.ROOT / "samples"
LOCK = SAMPLES / ".samples.lock"
_CODECS = ("pcm_s16le", "pcm_f32le")


def entries() -> list[dict[str, str]]:
    """The manifest rows as dicts (``set``/``file``/``url``/``license``)."""
    if not MANIFEST.exists():
        raise SystemExit(f"missing {MANIFEST}")
    text = MANIFEST.read_text(encoding="utf-8")
    found = rows(text, ["set", "file", "url", "license"])
    if not found:
        raise SystemExit("samples/manifest.md: no table with set|file|url|license")
    out: list[dict[str, str]] = []
    for set_, file, url, license_ in found:
        if not (set_ and file and url):
            raise SystemExit(f"samples/manifest.md: incomplete row '{set_} {file}'")
        out.append({"set": set_, "file": file, "url": url, "license": license_})
    return out


def local_path(entry: dict[str, str]) -> Path:
    """Where a manifest entry lives on disk (``samples/<set>/<file>``)."""
    return SAMPLES / entry["set"] / entry["file"]


def fetch(force: bool = False) -> list[Path]:
    """Download every manifest file that is missing (or all of them, if *force*)."""
    written: list[Path] = []
    for entry in entries():
        dest = local_path(entry)
        if dest.exists() and not force:
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        print(f"fetch   samples/{entry['set']}/{entry['file']}")
        urllib.request.urlretrieve(entry["url"], dest)
        written.append(dest)
    return written


def _probe(path: Path) -> dict:
    """ffprobe the first audio stream, as a dict."""
    args = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "a:0",
        "-show_entries",
        "stream=codec_name,sample_rate",
        "-of",
        "json",
        str(path),
    ]
    out = subprocess.run(args, capture_output=True, text=True).stdout
    try:
        return json.loads(out or "{}")
    except json.JSONDecodeError:
        return {}


def _canonical(path: Path) -> bool:
    """True if *path* is already 48 kHz PCM (so ``prepare`` can skip it)."""
    streams = _probe(path).get("streams") or []
    if not streams:
        return False
    stream = streams[0]
    return (
        stream.get("codec_name") in _CODECS
        and str(stream.get("sample_rate")) == "48000"
    )


def prepare(force: bool = False) -> list[Path]:
    """Normalise every sample to 48 kHz PCM (skip ones already canonical)."""
    written: list[Path] = []
    for entry in entries():
        src = local_path(entry)
        if not src.exists():
            raise SystemExit(
                f"samples/manifest.md: {src} is missing (run `fftechno samples`)"
            )
        if not force and _canonical(src):
            continue
        print(f"prepare samples/{entry['set']}/{entry['file']}")
        tmp = src.with_suffix(".tmp.wav")
        ffmpeg(["-y", "-i", str(src), "-ar", "48000", "-c:a", "pcm_s16le", str(tmp)])
        tmp.replace(src)
        written.append(src)
    return written


def run(force: bool = False) -> None:
    """``python -m fftechno samples``: fetch then prepare, under one lock."""
    with build_lock(LOCK):
        fetch(force=force)
        prepare(force=force)
    print(f"samples ready under {SAMPLES}")
