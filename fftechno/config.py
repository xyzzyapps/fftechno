"""Global configuration: paths and constants shared by every song.

Anything *song-specific* lives under ``songs/<name>/`` (``song.md``, ``sounds.md``,
``vocals.md``, ``video.md``) and is exposed through ``fftechno.song.Song``. Nothing
in this module mentions a particular track.
"""

from __future__ import annotations

import os
from pathlib import Path

# --- root paths ------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
SONGS = ROOT / "songs"  # songs/<name>/...
DEFAULT_SONG = "basement"
FILTERS = ROOT / "filters"  # per song: filters/<name>/
OUTPUT = ROOT / "output"  # per song: output/<name>/
TOOLS = ROOT / "tools"
TEMPLATES = ROOT / "templates"
IMAGES = ROOT / "ascii"
VISUALIZER = ROOT / "fftechno" / "visualizer.vpy"


def _vspipe() -> Path:
    """Prefer an explicit path, then the vspipe next to libvapoursynth.dll."""
    override = os.environ.get("FFTECHNO_VSPIPE")
    if override:
        return Path(override)
    for candidate in (
        ROOT / ".venv" / "Lib" / "site-packages" / "vapoursynth" / "vspipe.exe",
        ROOT / ".venv" / "Scripts" / "vspipe.exe",
    ):
        if candidate.exists():
            return candidate
    return ROOT / ".venv" / "Scripts" / "vspipe.exe"


VSPIPE = _vspipe()

# --- video (generic) -------------------------------------------------------
VIDEO_W, VIDEO_H, VIDEO_FPS = 1920, 1080, 30

# --- models (shared) -------------------------------------------------------
GIRL_MODEL = Path(
    os.environ.get("FFTECHNO_RVM_MODEL", TOOLS / "rvm" / "rvm_mobilenetv3_fp32.onnx")
)  # Robust Video Matting
GIRL_MATTE_DOWNSCALE = 0.5
PIPER = Path(os.environ.get("FFTECHNO_PIPER", TOOLS / "piper" / "piper.exe"))
PIPER_VOICES = Path(os.environ.get("FFTECHNO_PIPER_VOICES", TOOLS / "piper" / "voices"))
PIPER_SR = 22050
KITTEN_MODEL = os.environ.get("FFTECHNO_KITTEN_MODEL", "KittenML/kitten-tts-nano-0.8")
KITTEN_CACHE = os.environ.get("FFTECHNO_KITTEN_CACHE", str(TOOLS / "kitten"))
KITTEN_SR = 24000

# --- loudness targets ------------------------------------------------------
LOUDNESS_I = -13.0  # integrated LUFS
LOUDNESS_TP = -1.0  # true-peak target
LOUDNESS_LRA = 11.0
LIMITER_CEILING = 0.88  # linear amplitude (~ -1.1 dBFS)

# --- master chain (overridable per song via the Effects table) -------------
MASTER_SR = 48000
MASTER_EQ_F = 9000.0
MASTER_EQ_G = 1.5
MASTER_EQ_W = 0.7

# --- video encode defaults -------------------------------------------------
VIDEO_CRF = 20
VIDEO_PRESET = "slow"
VIDEO_TUNE = "film"
VIDEO_AUDIO_BITRATE = "192k"
PREVIEW_CRF = 22
PREVIEW_PRESET = "medium"
PREVIEW_AUDIO_BITRATE = "160k"
BOOST_CEILING = 0.70
GIRL_CRF = 20
GIRL_PRESET = "slow"
IO_RETRIES = 20
IO_RETRY_SECONDS = 0.5

# --- ear protection (off by default; opt in with --safe) -------------------
SAFE_CEILING = 0.5  # linear ceiling when --safe is on (~ -6 dBFS)


def unique_path(path: Path) -> Path:
    """Return *path*, or ``name_v2.ext`` / ``_v3`` ... if it already exists.

    Existing renders are never overwritten; a fresh name is chosen instead.
    """
    if not path.exists():
        return path
    version = 2
    while True:
        candidate = path.with_name(f"{path.stem}_v{version}{path.suffix}")
        if not candidate.exists():
            return candidate
        version += 1
