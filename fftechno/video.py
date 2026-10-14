"""Video build for a song: pipe VapourSynth into ffmpeg, mux the audio, re-level.

The picture is a `Look` (``fftechno/looks.py``) and the treatment is an ordered
effect chain (``fftechno/effects.py``). Before rendering, every instrument the
chain needs is baked into ``logs/fx/<stem>.wav`` with its section automation from
``song.md`` applied, so a visual reacts to what is actually *audible*.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

from . import arrangement
from . import config as C
from . import effects as fx
from .looks import get_look
from .proc import ffmpeg
from .song import Song


def effect_names(song: Song, override: str | list[str] | None = None) -> list[str]:
    """The effect chain for *song*: the CLI override, or ``video.md``, or default."""
    if override:
        names = (
            [n.strip() for n in override.split(",")]
            if isinstance(override, str)
            else list(override)
        )
        return [n for n in names if n]
    return list(song.video().effects) or list(fx.DEFAULT_CHAIN)


def prepare_envelopes(song: Song, chain: list[fx.Effect]) -> list[str]:
    """Bake each instrument the chain needs into ``logs/fx/<stem>.wav``.

    The stem's section automation (``song.md``) is applied first, so the envelope
    the visualizer analyses matches the mix - an instrument is silent while its
    section gain is `0.00`. Stems that were never rendered are skipped (that
    instrument's visual just stays silent). Returns the names that were prepared.
    """
    wanted = fx.required_instruments(chain)
    if not wanted:
        return []
    parsed = song.arrangement()
    out_dir = song.logs / "fx"
    out_dir.mkdir(parents=True, exist_ok=True)
    ready: list[str] = []
    for name in wanted:
        stem = song.stems / f"{name}.wav"
        if not stem.exists():
            print(f"  no stem for '{name}': its visual will stay silent")
            continue
        expr = arrangement.gain_expr(parsed, name) if name in parsed.arranged else "1.0"
        ffmpeg(
            [
                "-y",
                "-i",
                str(stem),
                "-af",
                f"volume=volume='{expr}':eval=frame",
                "-ac",
                "1",
                "-c:a",
                "pcm_s16le",
                str(out_dir / f"{name}.wav"),
            ]
        )
        ready.append(name)
    return ready


def write_fx_spec(song: Song, chain: list[fx.Effect], instruments: list[str]) -> Path:
    """Serialise the effect chain for the visualizer (``logs/fx.json``)."""
    desc = f"{song.name} / {song.video().look} / " + (
        ", ".join(e.name for e in chain) or "no effects"
    )
    spec = fx.to_spec(chain, instruments, desc)
    path = song.logs / "fx.json"
    path.write_text(json.dumps(spec, indent=1), encoding="utf-8")
    return path


def _render_and_mux(
    song: Song,
    audio: Path,
    *,
    look: str,
    mode: str,
    fx_spec: Path | None = None,
    static: bool = False,
) -> Path:
    """Run vspipe -> ffmpeg (H.264 + AAC) into a new master MP4 for *song*.

    The audio path, the picture data, the effect chain and the Pollock accumulation
    mode are handed to the visualizer through the environment. Returns the path
    written (never overwrites an old render)."""
    if not C.VSPIPE.exists():
        raise SystemExit(f"vspipe not found at {C.VSPIPE} (create the venv first)")

    sprites = str(song.girl_sprites) if get_look(look).emits == "sprites" else ""
    pick = str(song.girl_pick) if sprites else ""
    frame = song.video()
    env = dict(
        os.environ,
        FFTECHNO_STATIC="1" if static else "0",
        FFTECHNO_AUDIO=str(audio),
        FFTECHNO_W=str(frame.width),
        FFTECHNO_H=str(frame.height),
        FFTECHNO_GIRL_FRAMES=str(song.girl_frames),
        FFTECHNO_GIRL_SPRITES=sprites,
        FFTECHNO_GIRL_PICK=pick,
        FFTECHNO_POLLOCK=(mode if look == "pollock" else ""),
        FFTECHNO_LYRICS=(str(song.lyrics) if song.lyrics.exists() else ""),
        FFTECHNO_FX=(str(fx_spec) if fx_spec else ""),
        FFTECHNO_ENV_DIR=str(song.logs / "fx"),
        FFTECHNO_ROOT=str(C.ROOT),
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
    """Downscale the master into a new web-friendly 720p-class preview."""
    width, height = song.video().preview
    out = C.unique_path(song.preview_video)
    ffmpeg(
        [
            "-y",
            "-i",
            str(master),
            "-vf",
            f"scale={width}:{height}",
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


def swap_audio(
    song: Song, audio: Path | None = None, targets: tuple[Path, ...] | None = None
) -> None:
    """Replace the audio of the rendered MP4(s) with the current master.

    The video stream is **copied** - no frame is re-encoded - so this is the way to
    apply an audio-only change. Unlike :func:`re_level` it applies no gain and no
    limiter: the master is muxed as it is.
    """
    audio = audio or song.audio
    if targets is None:
        targets = tuple(
            t for t in (song.master_video, song.preview_video) if t.exists()
        )
    for target in targets:
        if not target.exists():
            continue
        tmp = song.logs / f"{target.stem}__swap.mp4"
        ffmpeg(
            [
                "-y",
                "-i",
                str(target),
                "-i",
                str(audio),
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
        print(f"swapped audio: {target}")


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
    fx_chain: str | list[str] | None = None,
) -> None:
    """Render *song*'s video, make the preview, and optionally re-level to *boost*."""
    video = song.video()
    look = look or video.look
    if mode is None:
        mode = get_look(look).accumulation or "trail"
    audio = audio or song.audio

    chain = fx.build_chain(
        effect_names(song, fx_chain), video.params, song.arrangement().stems_order
    )
    print("effects: " + (", ".join(e.name for e in chain) or "none"))
    ready = prepare_envelopes(song, chain)
    if ready:
        print("instruments: " + ", ".join(ready))
    for effect in chain:  # an effect only sees instruments that were prepared
        effect.required = tuple(n for n in effect.required if n in ready)
    spec = write_fx_spec(song, chain, ready)

    master = _render_and_mux(
        song, audio, look=look, mode=mode, fx_spec=spec, static=static
    )
    print(f"video: {master}")
    preview = _preview(song, master)
    print(f"preview: {preview}")
    if boost and boost != 1.0:
        re_level(boost, song, audio=audio, targets=(master, preview))
