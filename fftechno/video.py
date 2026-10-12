"""Video build for a song: pipe VapourSynth into ffmpeg, mux the audio, re-level."""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

from . import config as C
from .proc import ffmpeg
from .song import Song


def _render_and_mux(
    song: Song, audio: Path, *, look: str, mode: str, static: bool = False
) -> Path:
    """Run vspipe -> ffmpeg (H.264 + AAC) into a new master MP4 for *song*.

    The audio path, the picture data and the Pollock accumulation mode are handed
    to the visualizer through the environment. Returns the path written (never
    overwrites an old render)."""
    if not C.VSPIPE.exists():
        raise SystemExit(f"vspipe not found at {C.VSPIPE} (create the venv first)")

    sprites = str(song.girl_sprites) if look == "outline" else ""
    pick = str(song.girl_pick) if look == "outline" else ""
    env = dict(
        os.environ,
        FFTECHNO_STATIC="1" if static else "0",
        FFTECHNO_AUDIO=str(audio),
        FFTECHNO_GIRL_FRAMES=str(song.girl_frames),
        FFTECHNO_GIRL_SPRITES=sprites,
        FFTECHNO_GIRL_PICK=pick,
        FFTECHNO_POLLOCK=(mode if look == "pollock" else ""),
        FFTECHNO_LYRICS=(str(song.lyrics) if song.lyrics.exists() else ""),
    )
    song.output.mkdir(parents=True, exist_ok=True)
    out = C.unique_path(song.master_video)
    with (
        open(song.logs / "vspipe.log", "wb") as vlog,
        open(song.logs / "ffmpeg_video.log", "wb") as flog,
    ):
        vsp = subprocess.Popen(
            [str(C.VSPIPE), "-c", "y4m", str(C.VISUALIZER), "-"],
            stdout=subprocess.PIPE,
            stderr=vlog,
            env=env,
        )
        enc = subprocess.Popen(
            [
                "ffmpeg",
                "-hide_banner",
                "-y",
                "-f",
                "yuv4mpegpipe",
                "-i",
                "-",
                "-i",
                str(audio),
                "-c:v",
                "libx264",
                "-preset",
                "slow",
                "-crf",
                "20",
                "-tune",
                "film",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-shortest",
                "-movflags",
                "+faststart",
                str(out),
            ],
            stdin=vsp.stdout,
            stderr=flog,
        )
        vsp.stdout.close()  # allow vspipe to receive SIGPIPE if ffmpeg dies
        enc.wait()
        vsp.wait()
    if enc.returncode != 0:
        raise SystemExit(f"video encode failed ({enc.returncode}); see output/logs")
    return out


def _preview(song: Song, master: Path) -> Path:
    """Downscale the master into a new web-friendly 720p preview."""
    out = C.unique_path(song.preview_video)
    ffmpeg(
        [
            "-y",
            "-i",
            str(master),
            "-vf",
            "scale=1280:720",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "22",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-movflags",
            "+faststart",
            str(out),
        ]
    )
    return out


def re_level(
    factor: float,
    song: Song,
    audio: Path | None = None,
    targets: tuple[Path, ...] | None = None,
    ceiling: float = 0.70,
) -> None:
    """Re-encode MP4 audio at *factor* gain (video copied), limiter-bounded."""
    audio = audio or song.audio
    if targets is None:
        targets = tuple(
            t for t in (song.master_video, song.preview_video) if t.exists()
        )
    boost = song.logs / "boost.wav"
    ffmpeg(
        [
            "-y",
            "-i",
            str(audio),
            "-af",
            f"volume={factor},alimiter=limit={ceiling}:level=disabled",
            "-c:a",
            "pcm_s16le",
            str(boost),
        ]
    )
    for target in targets:
        if not target.exists():
            continue
        tmp = song.logs / f"{target.stem}__rel.mp4"
        ffmpeg(
            [
                "-y",
                "-i",
                str(target),
                "-i",
                str(boost),
                "-map",
                "0:v",
                "-map",
                "1:a",
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-shortest",
                "-movflags",
                "+faststart",
                str(tmp),
            ]
        )
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


def build(
    song: Song,
    audio: Path | None = None,
    look: str | None = None,
    mode: str | None = None,
    boost: float = 1.0,
    static: bool = False,
) -> None:
    """Render *song*'s video, make the preview, and optionally re-level to *boost*."""
    look = look or song.video().look
    if mode is None:
        from .looks import get_look

        mode = get_look(look).accumulation or "trail"
    audio = audio or song.audio
    master = _render_and_mux(song, audio, look=look, mode=mode, static=static)
    print(f"video: {master}")
    preview = _preview(song, master)
    print(f"preview: {preview}")
    if boost and boost != 1.0:
        re_level(boost, song, audio=audio, targets=(master, preview))
