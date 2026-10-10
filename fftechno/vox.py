"""Speech vocal stem: espeak-ng phrases processed and placed by filters/vox.txt."""

from __future__ import annotations

from . import config as C
from .proc import ffmpeg, run


def render() -> None:
    """Synthesize each phrase with espeak-ng, then place them into stems/vox.wav."""
    if not C.ESPEAK.exists():
        raise SystemExit(f"espeak-ng not found at {C.ESPEAK}")

    C.LOGS.mkdir(parents=True, exist_ok=True)
    raw: list[str] = []
    for i, phrase in enumerate(C.VOX_PHRASES):
        wav = C.LOGS / f"vox_{i}.wav"
        run([C.ESPEAK, "--path", C.ESPEAK_DATA, "-v", C.VOX_VOICE,
             "-w", wav, "-s", C.VOX_SPEED, "-p", C.VOX_PITCH, phrase])
        raw += ["-i", str(wav)]

    ffmpeg(["-y", *raw, "-filter_complex_script", C.FILTERS / "vox.txt",
            "-map", "[out]", "-c:a", "pcm_f32le", C.STEMS / "vox.wav"])
