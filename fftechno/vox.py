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

# Remove the silence the TTS pads onto the front of a phrase, so it can be placed
# exactly on its time (see `placement_graph`).
_TRIM_LEAD = "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.005"


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


def _wav_rate(path) -> int:
    """Sample rate of a wav (flite voices differ: kal is 8 kHz, the rest 16 kHz)."""
    out = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=sample_rate",
            "-of",
            "csv=p=0",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    return int(out)


def _say_flite(text: str, wav, voice: str) -> int:
    """FFmpeg's built-in TTS (libflite) - no model files, no network.

    Voices: ``slt`` (female), ``kal`` / ``kal16`` (male, 8 kHz), ``rms``, ``awb``.
    Like every TTS it pads leading silence, so ``trim_lead`` still applies."""
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-v",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"flite=text='{text}':voice={voice}",
            "-ac",
            "1",
            "-c:a",
            "pcm_s16le",
            str(wav),
        ],
        check=True,
    )
    return _wav_rate(wav)


_ENGINES = {"kitten": _say_kitten, "piper": _say_piper, "flite": _say_flite}


def placement_graph(
    lines: list[tuple[str, float]], sr: int, duration: float, trim_lead: bool = False
) -> str:
    """The ``-filter_complex`` body placing each line (one input per line).

    The TTS pads leading silence onto every phrase (about 0.65 s for Kitten), so
    without *trim_lead* a phrase sounds that much after its ``time``. With it the
    silence is removed first, so the phrase starts exactly on its time.
    """
    treat = _treat(sr)
    head = f"{_TRIM_LEAD}," if trim_lead else ""
    parts = [
        f"[{k}]{head}{treat},adelay={round(t * 1000)}:all=1[d{k}]"
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
    graph = placement_graph(vocals.lines, sr, song.duration, vocals.trim_lead)
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
