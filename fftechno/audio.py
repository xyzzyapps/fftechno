"""Audio build: render the stems, mix them, and master with 2-pass loudnorm.

All sound is produced by ffmpeg from the filter graphs in ``filters/``. The
master stage measures the mix with loudnorm and feeds the measured values back
into a second, linear pass, so ``filters/master.txt`` is no longer needed.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from . import arrangement
from . import config as C
from .proc import ffmpeg


def make_ir() -> None:
    """Generate the convolution reverb impulse response (decaying noise)."""
    expr = "(random(0)*2-1)*exp(-2.2*t)|(random(1)*2-1)*exp(-2.4*t)"
    ffmpeg(["-y", "-f", "lavfi", "-i", f"aevalsrc='{expr}':s=48000:d=2.2",
            "-c:a", "pcm_f32le", C.IR])


def render_osc_stems() -> None:
    """Render every oscillator stem from its filter graph."""
    C.STEMS.mkdir(parents=True, exist_ok=True)
    for name in C.OSC_STEMS:
        ffmpeg(["-y", "-filter_complex_script", C.FILTERS / f"{name}.txt",
                "-map", "[out]", "-c:a", "pcm_f32le", C.STEMS / f"{name}.wav"])


def _mix_inputs() -> list[str]:
    """-i arguments for the mix, in the order filters/mix.txt expects."""
    files = [C.STEMS / f"{name}.wav" for name in C.MIX_INPUTS] + [C.IR]
    args: list[str] = []
    for path in files:
        args += ["-i", str(path)]
    return args


def mix() -> None:
    """Mix the stems using the arrangement parsed from ``song.md``.

    The per-stem section automation (plus panning, kick side-chain and reverb
    bus) is generated into ``output/logs/mix.txt`` and applied as a filtergraph.
    """
    graph = arrangement.build_graph(arrangement.parse(C.SONG))
    C.LOGS.mkdir(parents=True, exist_ok=True)
    script = C.LOGS / "mix.txt"
    script.write_text(graph, encoding="utf-8")
    ffmpeg(["-y", *_mix_inputs(), "-filter_complex_script", script,
            "-map", "[out]", "-c:a", "pcm_f32le", C.MIX_PRE])


def _measure(path: Path) -> dict[str, str]:
    """Run loudnorm in measurement mode and return its JSON metrics."""
    args = ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af",
            (f"loudnorm=I={C.LOUDNESS_I}:TP={C.LOUDNESS_TP}:LRA={C.LOUDNESS_LRA}"
             ":print_format=json"), "-f", "null", "-"]
    stderr = subprocess.run(args, capture_output=True, text=True).stderr
    match = re.search(r"\{[^{}]*\}", stderr, re.S)
    if not match:
        raise SystemExit("could not parse loudnorm measurements")
    return json.loads(match.group(0))


def master() -> None:
    """Two-pass linear loudness normalisation + limiter + dither -> techno.wav."""
    m = _measure(C.MIX_PRE)
    graph = (
        f"[0]loudnorm=I={C.LOUDNESS_I}:TP={C.LOUDNESS_TP}:LRA={C.LOUDNESS_LRA}"
        f":measured_I={m['input_i']}:measured_TP={m['input_tp']}"
        f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}"
        f":offset={m['target_offset']}:linear=true:print_format=summary,"
        f"alimiter=limit={C.LIMITER_CEILING}:level=disabled,"
        "equalizer=f=9000:t=h:w=0.7:g=1.5,"
        "aresample=48000:out_sample_fmt=s16:dither_method=triangular_hp,"
        "aformat=sample_fmts=s16:channel_layouts=stereo[out]"
    )
    ffmpeg(["-y", "-i", C.MIX_PRE, "-filter_complex", graph,
            "-map", "[out]", "-c:a", "pcm_s16le", C.AUDIO])


def build() -> None:
    """Full audio pipeline: IR + vocals + stems -> mix -> master."""
    from . import vox  # imported here so audio-only use needs no espeak import cost

    make_ir()
    vox.render()
    render_osc_stems()
    mix()
    master()
