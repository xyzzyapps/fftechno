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
GIRL_SPRITES = OUTPUT / "girl_sprites.npy"  # outline look: RGB sprites (per source frame)
GIRL_PICK = OUTPUT / "girl_pick.npy"        # outline look: sprite index per output frame
GIRL_TOP_MARGIN = 70            # outline look: ignore the top rows (stage lights)
GIRL_LOOK = "pollock"           # "edge" | "pollock" | "outline"
GIRL_POLLOCK_MODE = "trail"     # "reset" | "trail" | "build" (paint accumulation)
GIRL_POLLOCK_ENV = "FFTECHNO_POLLOCK"        # set by video.py; read by the visualizer
GIRL_SPRITES_ENV = "FFTECHNO_GIRL_SPRITES"
GIRL_PICK_ENV = "FFTECHNO_GIRL_PICK"

# --- musical timing --------------------------------------------------------
BPM = 155                   # fallback; the video loop derives the BPM from song.md
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
# (phrase, start_seconds): the single source of truth for BOTH the vocal audio
# (placed by filters/vox.txt) and the on-screen lyrics.
_VOX_BAR = 60.0 / 155 * 4      # bar length at the track BPM
VOX_LINES = (
    ("go deep", 8 * _VOX_BAR),
    ("feel it", 24 * _VOX_BAR),
    ("seek yourself", 40 * _VOX_BAR),
    ("let go", 48 * _VOX_BAR),
    ("go deeper", 72 * _VOX_BAR),
    ("free your mind", 80 * _VOX_BAR),
    ("come alive", 112 * _VOX_BAR),
    ("know thyself", 128 * _VOX_BAR),
    ("rise up", 145 * _VOX_BAR),
)
VOX_VOICE = "slt"           # flite female voice (16 kHz mono output)
LYRICS = OUTPUT / "lyrics.json"        # written by vox; read by the visualizer

# --- ear protection (OFF by default; opt in with --safe) -------------------
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
