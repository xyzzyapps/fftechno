"""Video build: pipe VapourSynth into ffmpeg, mux the audio, and re-level."""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

from . import config as C
from .proc import ffmpeg


def _render_and_mux(audio: Path, *, static: bool = False) -> Path:
    """Run vspipe -> ffmpeg (H.264 + AAC) into a new master MP4.

    ``static=True`` tells the visualizer to emit a single frozen frame (no
    animation) via the ``FFTECHNO_STATIC`` environment variable. The audio and
    girl-frame paths are handed to the visualizer via the environment too.
    Returns the path actually written (never overwrites an old render).
    """
    if not C.VSPIPE.exists():
        raise SystemExit(f"vspipe not found at {C.VSPIPE} (create the venv first)")

    env = dict(os.environ, FFTECHNO_STATIC="1" if static else "0",
               FFTECHNO_AUDIO=str(audio), FFTECHNO_GIRL_FRAMES=str(C.GIRL_FRAMES))
    C.OUTPUT.mkdir(parents=True, exist_ok=True)
    out = C.unique_path(C.MASTER_VIDEO)
    with open(C.LOGS / "vspipe.log", "wb") as vlog, \
            open(C.LOGS / "ffmpeg_video.log", "wb") as flog:
        vsp = subprocess.Popen(
            [str(C.VSPIPE), "-c", "y4m", str(C.VISUALIZER), "-"],
            stdout=subprocess.PIPE, stderr=vlog, env=env)
        enc = subprocess.Popen(
            ["ffmpeg", "-hide_banner", "-y", "-f", "yuv4mpegpipe", "-i", "-",
             "-i", str(audio), "-c:v", "libx264", "-preset", "slow", "-crf", "20",
             "-tune", "film", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
             "-shortest", "-movflags", "+faststart", str(out)],
            stdin=vsp.stdout, stderr=flog)
        vsp.stdout.close()          # allow vspipe to receive SIGPIPE if ffmpeg dies
        enc.wait()
        vsp.wait()
    if enc.returncode != 0:
        raise SystemExit(f"video encode failed ({enc.returncode}); see output/logs")
    return out


def _preview(master: Path) -> Path:
    """Downscale the master into a new web-friendly 720p preview."""
    out = C.unique_path(C.PREVIEW_VIDEO)
    ffmpeg(["-y", "-i", master, "-vf", "scale=1280:720",
            "-c:v", "libx264", "-preset", "medium", "-crf", "22",
            "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(out)])
    return out


def re_level(factor: float, audio: Path | None = None,
             targets: tuple[Path, ...] | None = None, ceiling: float = 0.70) -> None:
    """Re-encode MP4 audio at *factor* gain (video copied), limiter-bounded."""
    audio = audio or C.AUDIO
    if targets is None:
        targets = tuple(t for t in (C.MASTER_VIDEO, C.PREVIEW_VIDEO) if t.exists())
    boost = C.LOGS / "boost.wav"
    ffmpeg(["-y", "-i", str(audio), "-af",
            f"volume={factor},alimiter=limit={ceiling}:level=disabled",
            "-c:a", "pcm_s16le", str(boost)])

    for target in targets:
        if not target.exists():
            continue
        tmp = C.LOGS / f"{target.stem}__rel.mp4"
        ffmpeg(["-y", "-i", str(target), "-i", str(boost), "-map", "0:v", "-map", "1:a",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                "-movflags", "+faststart", str(tmp)])
        _replace(tmp, target)


def _replace(src: Path, dst: Path, attempts: int = 20) -> None:
    """Replace *dst* with *src*, retrying through transient Windows file locks."""
    for _ in range(attempts):
        try:
            src.replace(dst)
            return
        except PermissionError:
            time.sleep(0.5)
    raise SystemExit(f"could not replace {dst} (file locked by another process?)")


def build(*, audio: Path | None = None, boost: float = 1.0, static: bool = False) -> None:
    """Render the video, make the preview, and optionally re-level to *boost*.

    Uses the mastered WAV at *audio* (defaults to the canonical ``techno.wav``).
    ``static=True`` renders a single frozen frame for the whole duration.
    """
    audio = audio or C.AUDIO
    master = _render_and_mux(audio, static=static)
    print(f"video: {master}")
    preview = _preview(master)
    print(f"preview: {preview}")
    if boost and boost != 1.0:
        re_level(boost, audio=audio, targets=(master, preview))
