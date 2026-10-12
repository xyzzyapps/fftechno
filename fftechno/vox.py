"""Speech vocal stem: ffmpeg's built-in flite synthesises each phrase, then
``filters/vox.txt`` processes and places them into ``stems/vox.wav``.

The voice is generated entirely by ffmpeg (the ``flite`` filter) - no external
TTS binary is required.
"""

from __future__ import annotations

from . import config as C
from .proc import ffmpeg


def render() -> None:
    """Synthesize each phrase with ffmpeg's flite filter, then place them into
    ``stems/vox.wav`` via the ``filters/vox.txt`` placement graph."""
    C.LOGS.mkdir(parents=True, exist_ok=True)
    raw: list[str] = []
    for i, phrase in enumerate(C.VOX_PHRASES):
        wav = C.LOGS / f"vox_{i}.wav"
        ffmpeg(["-y", "-f", "lavfi",
                "-i", f"flite=text='{phrase}':voice={C.VOX_VOICE}",
                "-c:a", "pcm_s16le", wav])
        raw += ["-i", str(wav)]

    ffmpeg(["-y", *raw, "-/filter_complex", str(C.FILTERS / "vox.txt"),
            "-map", "[out]", "-c:a", "pcm_f32le", C.STEMS / "vox.wav"])
