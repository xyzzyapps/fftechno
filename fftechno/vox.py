"""Speech vocal stem.

A local neural TTS - **Kitten TTS** (``kittenml`` + the nano ONNX model) or
**Piper** - synthesises each short phrase, then ``filters/vox.txt`` places them at
the times in ``config.VOX_LINES``; the same list is written to
``output/lyrics.json`` so the video can draw the on-screen lyrics at exactly the
same moments. Both engines run offline; select with ``config.VOX_ENGINE`` or
``python -m fftechno audio --tts kitten|piper``.
"""

from __future__ import annotations

import json
import subprocess

from . import config as C
from .proc import ffmpeg

_KITTEN = None      # cached KittenTTS model (loading is slow)


def _treat(sr: int) -> str:
    """Voice shaping for a source at *sr* Hz: ~ +1.5 semitones (younger /
    feminine, duration preserved with atempo), a mid-forward tone and a hint of
    grit for a "punk teenager" feel."""
    ratio = 1.09
    return (f"asetrate={int(sr * ratio)},aresample=48000,atempo={1 / ratio:.4f},"
            "highpass=f=140,"
            "equalizer=f=2400:t=q:w=1.2:g=3,equalizer=f=350:t=q:w=1:g=-3,"
            "asoftclip=type=tanh:threshold=0.9,"
            "aecho=0.8:0.7:55|110:0.28|0.14,lowpass=f=8500,volume=2.5")


def _kitten_model():
    """Load (and cache) the Kitten TTS ONNX model."""
    global _KITTEN
    if _KITTEN is None:
        from kittenml import KittenTTS
        _KITTEN = KittenTTS(C.KITTEN_MODEL, cache_dir=C.KITTEN_CACHE)
    return _KITTEN


def _say_kitten(text: str, wav) -> int:
    """Synthesize *text* with Kitten TTS; return the sample rate."""
    import soundfile as sf
    audio = _kitten_model().generate(text, voice=C.KITTEN_VOICE, speed=C.KITTEN_SPEED)
    sf.write(str(wav), audio, C.KITTEN_SR)
    return C.KITTEN_SR


def _say_piper(text: str, wav) -> int:
    """Synthesize *text* with Piper (text on stdin); return the sample rate."""
    if not C.PIPER.exists():
        raise SystemExit(f"piper not found at {C.PIPER}; see SPEC.md")
    subprocess.run([str(C.PIPER), "--model", str(C.PIPER_VOICE),
                    "--output_file", str(wav)],
                   input=text.encode("utf-8"), check=True)
    return C.PIPER_SR


_ENGINES = {"kitten": _say_kitten, "piper": _say_piper}


def placement_graph(sr: int) -> str:
    """The ``-filter_complex`` body that places each phrase in time."""
    treat = _treat(sr)
    lines = [f"[{i}]{treat},adelay={int(round(t * 1000))}:all=1[d{i}]"
             for i, (_text, t) in enumerate(C.VOX_LINES)]
    mixes = "".join(f"[d{i}]" for i in range(len(C.VOX_LINES)))
    lines.append(f"{mixes}amix=inputs={len(C.VOX_LINES)}:normalize=0,"
                 f"apad=whole_dur={C.DURATION:g}[out]")
    return ";\n".join(lines) + "\n"


def write_lyrics() -> None:
    """Write the ``[[text, start], ...]`` list the visualizer draws on screen."""
    C.LYRICS.write_text(json.dumps([[t, round(s, 3)] for t, s in C.VOX_LINES]),
                        encoding="utf-8")


def render(engine: str | None = None) -> None:
    """Synthesize each phrase and place them into ``stems/vox.wav``."""
    engine = engine or C.VOX_ENGINE
    if engine not in _ENGINES:
        raise SystemExit(f"unknown TTS engine '{engine}' (use 'kitten' or 'piper')")
    say = _ENGINES[engine]
    C.LOGS.mkdir(parents=True, exist_ok=True)
    raw: list[str] = []
    sr = C.KITTEN_SR
    for i, (text, _t) in enumerate(C.VOX_LINES):
        wav = C.LOGS / f"vox_{i}.wav"
        sr = say(text, wav)
        raw += ["-i", str(wav)]
    graph = placement_graph(sr)
    (C.FILTERS / "vox.txt").write_text(graph, encoding="utf-8")
    ffmpeg(["-y", *raw, "-/filter_complex", str(C.FILTERS / "vox.txt"),
            "-map", "[out]", "-c:a", "pcm_f32le", C.STEMS / "vox.wav"])
    write_lyrics()
