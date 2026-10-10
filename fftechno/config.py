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
SONG = ROOT / "song.md"
MASTER_VIDEO = OUTPUT / "techno_visualizer.mp4"
PREVIEW_VIDEO = OUTPUT / "techno_visualizer_720p.mp4"

VISUALIZER = ROOT / "visualizer.vpy"
VSPIPE = ROOT / ".venv" / "Scripts" / "vspipe.exe"
ESPEAK = TOOLS / "espeak-ng" / "eSpeak NG" / "espeak-ng.exe"
ESPEAK_DATA = TOOLS / "espeak-ng" / "eSpeak NG" / "espeak-ng-data"

# --- musical timing --------------------------------------------------------
BPM = 140
BEAT = 60.0 / BPM
BAR = BEAT * 4
DURATION = 240.0            # seconds (4 minutes)

# --- video -----------------------------------------------------------------
VIDEO_W, VIDEO_H, VIDEO_FPS = 1920, 1080, 30

# --- loudness targets ------------------------------------------------------
LOUDNESS_I = -13.0          # integrated LUFS
LOUDNESS_TP = -1.0          # true-peak target
LOUDNESS_LRA = 11.0
LIMITER_CEILING = 0.88      # linear amplitude (~ -1.1 dBFS)

# --- assets ----------------------------------------------------------------
# Oscillator stems, each rendered from filters/<name>.txt (ends in [out]).
OSC_STEMS = (
    "kick", "clap", "hat", "ohat", "perc", "shaker",
    "bongo", "rim", "bass", "growl", "acid", "beeps",
)

# Input order for filters/mix.txt ([0]..[n]); the reverb IR is appended last.
MIX_INPUTS = (
    "kick", "clap", "hat", "ohat", "perc", "bass", "growl",
    "acid", "shaker", "vox", "bongo", "rim", "beeps",
)

# Female espeak-ng phrases (order must match filters/vox.txt placement graph).
VOX_PHRASES = (
    "speak to me", "come on", "feel it", "hard groove", "let go",
    "trust me", "lock in", "take me higher", "hands up",
)
VOX_VOICE = "en+f4"
VOX_SPEED = "132"
VOX_PITCH = "70"
