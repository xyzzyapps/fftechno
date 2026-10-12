"""Audio build for a song: render the stems, mix them, master with 2-pass loudnorm.

All sound is produced by ffmpeg from the song's filter graphs (``filters/<song>/``).
The master stage measures the mix with loudnorm and feeds the measured values back
into a second, linear pass.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from . import arrangement
from . import config as C
from .proc import ffmpeg
from .song import Song


def make_ir(song: Song) -> None:
    """Generate the convolution reverb impulse response (decaying noise)."""
    expr = "(random(0)*2-1)*exp(-2.2*t)|(random(1)*2-1)*exp(-2.4*t)"
    song.logs.mkdir(parents=True, exist_ok=True)
    ffmpeg(
        [
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"aevalsrc='{expr}':s=48000:d=2.2",
            "-c:a",
            "pcm_f32le",
            song.ir,
        ]
    )


def render_stems(song: Song, names) -> None:
    """Render each synth (``filters/<song>/<name>.txt``) to ``stems/<name>.wav``."""
    song.stems.mkdir(parents=True, exist_ok=True)
    for name in names:
        ffmpeg(
            [
                "-y",
                "-/filter_complex",
                str(song.filters / f"{name}.txt"),
                "-map",
                "[out]",
                "-c:a",
                "pcm_f32le",
                song.stems / f"{name}.wav",
            ]
        )


def mix(song: Song) -> None:
    """Mix the stems using the song's arrangement (section automation, pan, ...)."""
    parsed = song.arrangement()
    script = song.logs / "mix.txt"
    song.logs.mkdir(parents=True, exist_ok=True)
    script.write_text(arrangement.build_graph(parsed), encoding="utf-8")

    inputs: list[str] = []
    for name in parsed.stems_order:
        inputs += ["-i", str(song.stems / f"{name}.wav")]
    inputs += ["-i", str(song.ir)]
    ffmpeg(
        [
            "-y",
            *inputs,
            "-/filter_complex",
            str(script),
            "-map",
            "[out]",
            "-c:a",
            "pcm_f32le",
            song.mix_pre,
        ]
    )


def _measure(path: Path) -> dict[str, str]:
    """Run loudnorm in measurement mode and return its JSON metrics."""
    args = [
        "ffmpeg",
        "-hide_banner",
        "-nostats",
        "-i",
        str(path),
        "-af",
        (
            f"loudnorm=I={C.LOUDNESS_I}:TP={C.LOUDNESS_TP}:LRA={C.LOUDNESS_LRA}"
            ":print_format=json"
        ),
        "-f",
        "null",
        "-",
    ]
    stderr = subprocess.run(args, capture_output=True, text=True).stderr
    match = re.search(r"\{[^{}]*\}", stderr, re.DOTALL)
    if not match:
        raise SystemExit("could not parse loudnorm measurements")
    return json.loads(match.group(0))


def master(song: Song, safe: bool = False) -> Path:
    """Two-pass linear loudness normalisation + limiter + dither -> techno.wav.

    ``safe=True`` adds an extra, stricter limiter (ear protection; OFF by default).
    Returns the path actually written (a versioned name if the target exists)."""
    m = _measure(song.mix_pre)
    guard = f"alimiter=limit={C.SAFE_CEILING:g}:level=disabled," if safe else ""
    graph = (
        f"[0]loudnorm=I={C.LOUDNESS_I}:TP={C.LOUDNESS_TP}:LRA={C.LOUDNESS_LRA}"
        f":measured_I={m['input_i']}:measured_TP={m['input_tp']}"
        f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}"
        f":offset={m['target_offset']}:linear=true:print_format=summary,"
        f"alimiter=limit={C.LIMITER_CEILING}:level=disabled,"
        + guard
        + "equalizer=f=9000:t=h:w=0.7:g=1.5,"
        "aresample=48000:out_sample_fmt=s16:dither_method=triangular_hp,"
        "aformat=sample_fmts=s16:channel_layouts=stereo[out]"
    )
    out = C.unique_path(song.audio)
    ffmpeg(
        [
            "-y",
            "-i",
            str(song.mix_pre),
            "-filter_complex",
            graph,
            "-map",
            "[out]",
            "-c:a",
            "pcm_s16le",
            str(out),
        ]
    )
    return out


def build(song: Song, safe: bool = False, tts: str | None = None) -> Path:
    """Full audio pipeline for *song*: synth defs + IR + vocals + stems -> mix -> master."""
    from . import synth, vox

    names = synth.generate(song)
    make_ir(song)
    if "vox" in song.arrangement().stems:
        vox.render(song, engine=tts)
    render_stems(song, names)
    mix(song)
    return master(song, safe=safe)
