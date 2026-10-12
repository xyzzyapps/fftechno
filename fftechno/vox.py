"""Speech vocal stem: ffmpeg's built-in ``flite`` filter synthesises each short
phrase, then ``filters/vox.txt`` places them at the times in
``config.VOX_LINES``; the same list is written to ``output/lyrics.json`` so the
video can draw the on-screen lyrics at exactly the same moments.
"""

from __future__ import annotations

import json

from . import config as C
from .proc import ffmpeg

# Pitch/echo/level applied to every flite phrase (flite emits 16 kHz mono).
_TREAT = ("asetrate=17000,aresample=48000,aecho=0.8:0.7:70|140:0.35|0.2,"
          "lowpass=7500,volume=1.6")


def placement_graph() -> str:
    """The ``-filter_complex`` body that places each phrase in time."""
    lines = [f"[{i}]{_TREAT},adelay={int(round(t * 1000))}:all=1[d{i}]"
             for i, (_text, t) in enumerate(C.VOX_LINES)]
    mixes = "".join(f"[d{i}]" for i in range(len(C.VOX_LINES)))
    lines.append(f"{mixes}amix=inputs={len(C.VOX_LINES)}:normalize=0,"
                 f"apad=whole_dur={C.DURATION:g}[out]")
    return ";\n".join(lines) + "\n"


def write_lyrics() -> None:
    """Write the ``[[text, start], ...]`` list the visualizer draws on screen."""
    C.LYRICS.write_text(json.dumps([[t, round(s, 3)] for t, s in C.VOX_LINES]),
                        encoding="utf-8")


def render() -> None:
    """Synthesize each phrase with flite and place them into ``stems/vox.wav``."""
    C.LOGS.mkdir(parents=True, exist_ok=True)
    raw: list[str] = []
    for i, (text, _t) in enumerate(C.VOX_LINES):
        wav = C.LOGS / f"vox_{i}.wav"
        ffmpeg(["-y", "-f", "lavfi", "-i", f"flite=text='{text}':voice={C.VOX_VOICE}",
                "-c:a", "pcm_s16le", wav])
        raw += ["-i", str(wav)]
    graph = placement_graph()
    (C.FILTERS / "vox.txt").write_text(graph, encoding="utf-8")
    ffmpeg(["-y", *raw, "-/filter_complex", str(C.FILTERS / "vox.txt"),
            "-map", "[out]", "-c:a", "pcm_f32le", C.STEMS / "vox.wav"])
    write_lyrics()
