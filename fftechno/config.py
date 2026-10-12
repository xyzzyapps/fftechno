"""Global configuration: paths and constants shared by every song.

Anything *song-specific* lives under ``songs/<name>/`` (``song.md``, ``sounds.md``,
``vocals.md``, ``video.md``) and is exposed through ``fftechno.song.Song``. Nothing
in this module mentions a particular track.
"""

from __future__ import annotations

from pathlib import Path

# --- root paths ------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
SONGS = ROOT / "songs"                  # songs/<name>/...
FILTERS = ROOT / "filters"              # per song: filters/<name>/
OUTPUT = ROOT / "output"                # per song: output/<name>/
TOOLS = ROOT / "tools"
TEMPLATES = ROOT / "templates"
IMAGES = ROOT / "ascii"
VISUALIZER = ROOT / "visualizer.vpy"


def _vspipe() -> Path:
    """Prefer the vspipe next to libvapoursynth.dll (the Scripts launcher can
    fail to find it on Windows)."""
    for candidate in (ROOT / ".venv" / "Lib" / "site-packages" / "vapoursynth" / "vspipe.exe",
                      ROOT / ".venv" / "Scripts" / "vspipe.exe"):
        if candidate.exists():
            return candidate
    return ROOT / ".venv" / "Scripts" / "vspipe.exe"


VSPIPE = _vspipe()

# --- video (generic) -------------------------------------------------------
VIDEO_W, VIDEO_H, VIDEO_FPS = 1920, 1080, 30
GIRL_FRAME_W, GIRL_FRAME_H = 960, 540   # size of the low-res picture the shader reads

# --- models (shared) -------------------------------------------------------
GIRL_MODEL = TOOLS / "rvm" / "rvm_mobilenetv3_fp32.onnx"   # Robust Video Matting
GIRL_MATTE_DOWNSCALE = 0.5
PIPER = TOOLS / "piper" / "piper.exe"
PIPER_VOICES = TOOLS / "piper" / "voices"
PIPER_SR = 22050
KITTEN_MODEL = "KittenML/kitten-tts-nano-0.8"
KITTEN_CACHE = str(TOOLS / "kitten")
KITTEN_SR = 24000

# --- loudness targets ------------------------------------------------------
LOUDNESS_I = -13.0          # integrated LUFS
LOUDNESS_TP = -1.0          # true-peak target
LOUDNESS_LRA = 11.0
LIMITER_CEILING = 0.88      # linear amplitude (~ -1.1 dBFS)

# --- ear protection (off by default; opt in with --safe) -------------------
SAFE_CEILING = 0.5          # linear ceiling when --safe is on (~ -6 dBFS)


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
