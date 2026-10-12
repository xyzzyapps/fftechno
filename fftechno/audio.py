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


def render_stems(names) -> None:
    """Render each synth (its ``filters/<name>.txt``) to ``output/stems/<name>.wav``."""
    C.STEMS.mkdir(parents=True, exist_ok=True)
    for name in names:
        ffmpeg(["-y", "-/filter_complex", str(C.FILTERS / f"{name}.txt"),
                "-map", "[out]", "-c:a", "pcm_f32le", C.STEMS / f"{name}.wav"])


def mix() -> None:
    """Mix the stems using the arrangement parsed from ``song.md``.

    The per-stem section automation (plus panning, side-chain and reverb bus) is
    generated into ``output/logs/mix.txt`` and applied as a filtergraph.
    """
    song = arrangement.parse(C.SONG)
    graph = arrangement.build_graph(song)
    C.LOGS.mkdir(parents=True, exist_ok=True)
    script = C.LOGS / "mix.txt"
    script.write_text(graph, encoding="utf-8")

    inputs: list[str] = []
    for name in song.stems_order:
        inputs += ["-i", str(C.STEMS / f"{name}.wav")]
    inputs += ["-i", str(C.IR)]
    ffmpeg(["-y", *inputs, "-/filter_complex", str(script),
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


def master() -> Path:
    """Two-pass linear loudness normalisation + limiter + dither -> techno.wav.

    Returns the path actually written (a ``_v2``/``_v3`` name if the target
    already exists, so old renders are preserved)."""
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
    out = C.unique_path(C.AUDIO)
    ffmpeg(["-y", "-i", C.MIX_PRE, "-filter_complex", graph,
            "-map", "[out]", "-c:a", "pcm_s16le", out])
    return out


def build() -> Path:
    """Full audio pipeline: synth defs + IR + vocals + stems -> mix -> master.

    Returns the path of the mastered WAV."""
    from . import synth, vox  # imported here so audio-only paths stay light

    names = synth.generate()        # sounds.md + templates -> filters/<name>.txt
    make_ir()
    if "vox" in arrangement.parse(C.SONG).stems:
        vox.render()
    render_stems(names)
    mix()
    return master()
