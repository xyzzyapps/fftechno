"""Video build: pipe VapourSynth into ffmpeg, mux the audio, and re-level."""

from __future__ import annotations

import subprocess
from pathlib import Path

from . import config as C
from .proc import ffmpeg


def _render_and_mux() -> None:
    """Run vspipe -> ffmpeg (H.264 + AAC) into the master MP4."""
    if not C.VSPIPE.exists():
        raise SystemExit(f"vspipe not found at {C.VSPIPE} (create the venv first)")

    C.OUTPUT.mkdir(parents=True, exist_ok=True)
    with open(C.LOGS / "vspipe.log", "wb") as vlog, \
            open(C.LOGS / "ffmpeg_video.log", "wb") as flog:
        vsp = subprocess.Popen(
            [str(C.VSPIPE), "-c", "y4m", str(C.VISUALIZER), "-"],
            stdout=subprocess.PIPE, stderr=vlog)
        enc = subprocess.Popen(
            ["ffmpeg", "-hide_banner", "-y", "-f", "yuv4mpegpipe", "-i", "-",
             "-i", str(C.AUDIO), "-c:v", "libx264", "-preset", "slow", "-crf", "20",
             "-tune", "film", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
             "-shortest", "-movflags", "+faststart", str(C.MASTER_VIDEO)],
            stdin=vsp.stdout, stderr=flog)
        vsp.stdout.close()          # allow vspipe to receive SIGPIPE if ffmpeg dies
        enc.wait()
        vsp.wait()
    if enc.returncode != 0:
        raise SystemExit(f"video encode failed ({enc.returncode}); see output/logs")


def _preview() -> None:
    """Downscale the master into a web friendly 720p preview."""
    ffmpeg(["-y", "-i", C.MASTER_VIDEO, "-vf", "scale=1280:720",
            "-c:v", "libx264", "-preset", "medium", "-crf", "22",
            "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", C.PREVIEW_VIDEO])


def re_level(factor: float, ceiling: float = 0.70) -> None:
    """Re-encode the MP4 audio at *factor* gain (video copied), limiter-bounded."""
    boost = C.LOGS / "boost.wav"
    ffmpeg(["-y", "-i", C.AUDIO, "-af",
            f"volume={factor},alimiter=limit={ceiling}:level=disabled",
            "-c:a", "pcm_s16le", boost])

    for target in (C.MASTER_VIDEO, C.PREVIEW_VIDEO):
        if not target.exists():
            continue
        tmp = C.LOGS / f"{target.stem}__rel.mp4"
        ffmpeg(["-y", "-i", target, "-i", boost, "-map", "0:v", "-map", "1:a",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                "-movflags", "+faststart", tmp])
        Path(tmp).replace(target)


def build(*, boost: float = 1.0) -> None:
    """Render the video, make the preview, and optionally re-level to *boost*."""
    _render_and_mux()
    _preview()
    if boost and boost != 1.0:
        re_level(boost)
