"""Project configuration: paths, timing constants and asset lists."""

from __future__ import annotations

from pathlib import Path

# --- paths -----------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
FILTERS = ROOT / "filters"
OUTPUT = ROOT / "output"
STEMS = OUTPUT / "stems"
LOGS = OUTPUT / "logs"
IMAGES = ROOT / "ascii"
TOOLS = ROOT / "tools"

AUDIO = OUTPUT / "techno.wav"
MIX_PRE = OUTPUT / "mix_pre.wav"
IR = LOGS / "ir.wav"
LOCK = LOGS / ".build.lock"
SONG = ROOT / "song.md"
SOUNDS = ROOT / "sounds.md"
TEMPLATES = ROOT / "templates"
MASTER_VIDEO = OUTPUT / "techno_visualizer.mp4"
PREVIEW_VIDEO = OUTPUT / "techno_visualizer_720p.mp4"

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

# --- dancing-girl visual (RVM matting -> edge detect -> beat-locked loop) ---
GIRL_MODEL = TOOLS / "rvm" / "rvm_mobilenetv3_fp32.onnx"   # Robust Video Matting
GIRL_MATTE_DOWNSCALE = 0.5        # RVM internal processing ratio (speed/quality)
GIRL_CROP_START = 2.0             # seconds into the source clip
GIRL_CROP_DURATION = 3.0          # seconds (== GIRL_LOOP_BEATS beats at BPM)
GIRL_LOOP_BEATS = 7               # loop length in beats
GIRL_FRAME_W, GIRL_FRAME_H = 960, 540   # stored frame stack size (16:9)
GIRL_FRAMES = OUTPUT / "girl_frames.npy"    # intermediate consumed by the video
GIRL_LOOP = OUTPUT / "girl_loop.mp4"        # standalone deliverable
GIRL_LOOK = "pollock"           # "edge" (matte + line drawing) | "pollock"
GIRL_POLLOCK_MODE = "trail"     # "reset" | "trail" | "build" (paint accumulation)
GIRL_POLLOCK_ENV = "FFTECHNO_POLLOCK"   # set by video.py; read by the visualizer

# --- musical timing --------------------------------------------------------
BPM = 140
BEAT = 60.0 / BPM
BAR = BEAT * 4
DURATION = 240.0            # seconds (4 minutes)
GIRL_LOOP_SECONDS = GIRL_LOOP_BEATS * BEAT   # 3.0 s exactly

# --- video -----------------------------------------------------------------
VIDEO_W, VIDEO_H, VIDEO_FPS = 1920, 1080, 30

# --- loudness targets ------------------------------------------------------
LOUDNESS_I = -13.0          # integrated LUFS
LOUDNESS_TP = -1.0          # true-peak target
LOUDNESS_LRA = 11.0
LIMITER_CEILING = 0.88      # linear amplitude (~ -1.1 dBFS)

# --- vocals (ffmpeg's built-in flite voice; no external TTS) ---------------
# Phrases in order; each is placed by filters/vox.txt at a fixed time.
VOX_PHRASES = (
    "speak to me", "come on", "feel it", "hard groove", "let go",
    "trust me", "lock in", "take me higher", "hands up",
)
VOX_VOICE = "slt"           # flite female voice (16 kHz mono output)


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
