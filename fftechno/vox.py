"""Speech vocal stem for a song.

A local neural TTS - **Kitten TTS** (``kittenml`` + the nano ONNX model) or
**Piper** - synthesises each phrase from the song's ``vocals.md``; the same
(text, time) list is written to ``lyrics.json`` for the video's on-screen lyrics.
Both engines run offline; the engine/voice come from ``vocals.md`` (overridable
with ``--tts``).
"""

from __future__ import annotations

import json
import subprocess

from . import config as C
from .proc import ffmpeg
from .song import Song

_KITTEN = None  # cached KittenTTS model (loading is slow)


def _treat(sr: int) -> str:
    """Voice shaping for a source at *sr* Hz: ~ +1.5 semitones (younger /
    feminine, duration preserved with atempo), a mid-forward tone and a hint of
    grit for a "punk teenager" feel."""
    ratio = 1.09
    return (
        f"asetrate={int(sr * ratio)},aresample=48000,atempo={1 / ratio:.4f},"
        "highpass=f=140,"
        "equalizer=f=2400:t=q:w=1.2:g=3,equalizer=f=350:t=q:w=1:g=-3,"
        "asoftclip=type=tanh:threshold=0.9,"
        "aecho=0.8:0.7:55|110:0.28|0.14,lowpass=f=8500,volume=2.5"
    )


def _kitten_model():
    global _KITTEN
    if _KITTEN is None:
        from kittenml import KittenTTS

        _KITTEN = KittenTTS(C.KITTEN_MODEL, cache_dir=C.KITTEN_CACHE)
    return _KITTEN


def _say_kitten(text: str, wav, voice: str) -> int:
    import soundfile as sf

    audio = _kitten_model().generate(text, voice=voice, speed=1.15)
    sf.write(str(wav), audio, C.KITTEN_SR)
    return C.KITTEN_SR


def _say_piper(text: str, wav, voice: str) -> int:
    model = C.PIPER_VOICES / f"{voice}.onnx"
    if not C.PIPER.exists() or not model.exists():
        raise SystemExit(f"piper/voice not found ({C.PIPER}, {model}); see SPEC.md")
    subprocess.run(
        [str(C.PIPER), "--model", str(model), "--output_file", str(wav)],
        input=text.encode("utf-8"),
        check=True,
    )
    return C.PIPER_SR


_ENGINES = {"kitten": _say_kitten, "piper": _say_piper}


def placement_graph(lines: list[tuple[str, float]], sr: int, duration: float) -> str:
    """The ``-filter_complex`` body placing each line (one input per line)."""
    treat = _treat(sr)
    parts = [
        f"[{k}]{treat},adelay={round(t * 1000)}:all=1[d{k}]"
        for k, (_text, t) in enumerate(lines)
    ]
    mixes = "".join(f"[d{k}]" for k in range(len(lines)))
    parts.append(
        f"{mixes}amix=inputs={len(lines)}:normalize=0,"
        f"apad=whole_dur={duration:g}[out]"
    )
    return ";\n".join(parts) + "\n"


def write_lyrics(song: Song, lines: list[tuple[str, float]]) -> None:
    song.lyrics.write_text(
        json.dumps([[t, round(s, 3)] for t, s in lines]), encoding="utf-8"
    )


def render(song: Song, engine: str | None = None) -> None:
    """Synthesize the song's phrases and place them into ``stems/vox.wav``."""
    vocals = song.vocals()
    if not vocals.lines:
        return
    engine = engine or vocals.engine
    if engine not in _ENGINES:
        raise SystemExit(f"unknown TTS engine '{engine}' (use 'kitten' or 'piper')")
    say = _ENGINES[engine]

    song.filters.mkdir(parents=True, exist_ok=True)
    song.logs.mkdir(parents=True, exist_ok=True)
    song.stems.mkdir(parents=True, exist_ok=True)

    wavs: dict[str, object] = {}
    sr = C.KITTEN_SR
    for i, text in enumerate(dict.fromkeys(t for t, _ in vocals.lines)):
        wav = song.logs / f"vox_{i}.wav"
        sr = say(text, wav, vocals.voice)
        wavs[text] = wav

    inputs: list[str] = []
    for text, _t in vocals.lines:
        inputs += ["-i", str(wavs[text])]
    graph = placement_graph(vocals.lines, sr, song.duration)
    (song.filters / "vox.txt").write_text(graph, encoding="utf-8")
    ffmpeg(
        [
            "-y",
            *inputs,
            "-/filter_complex",
            str(song.filters / "vox.txt"),
            "-map",
            "[out]",
            "-c:a",
            "pcm_f32le",
            str(song.stems / "vox.wav"),
        ]
    )
    write_lyrics(song, vocals.lines)
