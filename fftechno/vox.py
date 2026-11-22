"""Speech vocal stem for a song.

A local neural TTS - **Kitten TTS** (``kittenml`` + the nano ONNX model),
**Piper**, or ffmpeg's built-in **flite** - synthesises each phrase from the
song's ``vocals.md``; the same (text, time) list is written to ``lyrics.json`` for
the video's on-screen lyrics. All engines run offline; the engine/voice come from
``vocals.md`` (overridable with ``--tts``).
"""

from __future__ import annotations

import json
import subprocess

from . import config as C
from .proc import ffmpeg
from .song import Song

_KITTEN = None  # cached KittenTTS model (loading is slow)

# Voice treatment defaults; a song's vocals.md `## Parameters` table overrides them.
VOICE_DEFAULTS: dict[str, str] = {
    "pitch": "1.09",  # playback-rate ratio; atempo restores the duration
    "speed": "1.15",  # Kitten TTS speaking rate
    "highpass": "140",
    "mid_f": "2400",
    "mid_g": "3",
    "low_f": "350",
    "low_g": "-3",
    "drive": "0.9",
    "echo": "0.8:0.7:55|110:0.28|0.14",
    "lowpass": "8500",
    "volume": "2.5",
    "trim_db": "-45",
    "trim_silence": "0.005",
}


def _voice(params: dict[str, str] | None, key: str) -> str:
    """Return one voice parameter, falling back to ``VOICE_DEFAULTS``."""
    return (params or {}).get(key, VOICE_DEFAULTS[key])


def _treat(sr: int, params: dict[str, str] | None = None) -> str:
    """Voice shaping for a source at *sr* Hz.

    The defaults give ~ +1.5 semitones (younger/feminine, duration preserved with
    atempo), a mid-forward tone and a hint of grit. Every value is overridable from
    the song's ``vocals.md`` ``## Parameters`` table.
    """
    ratio = float(_voice(params, "pitch"))
    return (
        f"asetrate={int(sr * ratio)},aresample=48000,atempo={1 / ratio:.4f},"
        f"highpass=f={_voice(params, 'highpass')},"
        f"equalizer=f={_voice(params, 'mid_f')}:t=q:w=1.2:g={_voice(params, 'mid_g')},"
        f"equalizer=f={_voice(params, 'low_f')}:t=q:w=1:g={_voice(params, 'low_g')},"
        f"asoftclip=type=tanh:threshold={_voice(params, 'drive')},"
        f"aecho={_voice(params, 'echo')},"
        f"lowpass=f={_voice(params, 'lowpass')},volume={_voice(params, 'volume')}"
    )


def _kitten_model():
    """Load (and cache) the Kitten TTS model."""
    global _KITTEN
    if _KITTEN is None:
        from kittenml import KittenTTS

        _KITTEN = KittenTTS(C.KITTEN_MODEL, cache_dir=C.KITTEN_CACHE)
    return _KITTEN


def _say_kitten(
    text: str, wav, voice: str, params: dict[str, str] | None = None
) -> int:
    """Synthesise *text* with Kitten TTS and write a wav; returns its rate."""
    import soundfile as sf

    audio = _kitten_model().generate(
        text, voice=voice, speed=float(_voice(params, "speed"))
    )
    sf.write(str(wav), audio, C.KITTEN_SR)
    return C.KITTEN_SR


def _say_piper(text: str, wav, voice: str, params: dict[str, str] | None = None) -> int:
    """Synthesise *text* with a Piper voice and write a wav; returns its rate."""
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


def _say_flite(text: str, wav, voice: str, params: dict[str, str] | None = None) -> int:
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
    lines: list[tuple[str, float]],
    sr: int,
    duration: float,
    trim_lead: bool = False,
    params: dict[str, str] | None = None,
) -> str:
    """The ``-filter_complex`` body placing each line (one input per line).

    The TTS pads leading silence onto every phrase (about 0.65 s for Kitten), so
    without *trim_lead* a phrase sounds that much after its ``time``. With it the
    silence is removed first, so the phrase starts exactly on its time. *params*
    comes from the song's ``vocals.md`` and drives the treatment.
    """
    treat = _treat(sr, params)
    trim = (
        "silenceremove=start_periods=1:"
        f"start_threshold={_voice(params, 'trim_db')}dB:"
        f"start_silence={_voice(params, 'trim_silence')}"
    )
    head = f"{trim}," if trim_lead else ""
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
    """Write the (text, time) list as ``lyrics.json`` for the video."""
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
        raise SystemExit(
            f"unknown TTS engine '{engine}' (use 'kitten', 'piper' or 'flite')"
        )
    say = _ENGINES[engine]

    song.filters.mkdir(parents=True, exist_ok=True)
    song.logs.mkdir(parents=True, exist_ok=True)
    song.stems.mkdir(parents=True, exist_ok=True)

    wavs: dict[str, object] = {}
    sr = C.KITTEN_SR
    for i, text in enumerate(dict.fromkeys(t for t, _ in vocals.lines)):
        wav = song.logs / f"vox_{i}.wav"
        sr = say(text, wav, vocals.voice, vocals.params)
        wavs[text] = wav

    inputs: list[str] = []
    for text, _t in vocals.lines:
        inputs += ["-i", str(wavs[text])]
    graph = placement_graph(
        vocals.lines, sr, song.duration, vocals.trim_lead, vocals.params
    )
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
