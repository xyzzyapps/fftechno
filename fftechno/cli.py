"""Command line entry point for the fftechno build."""

from __future__ import annotations

import argparse
from pathlib import Path

from . import audio, video


def _latest(base: Path) -> Path:
    """Newest existing file matching *base* or its ``_vN`` versions."""
    candidates = sorted(base.parent.glob(f"{base.stem}*{base.suffix}"))
    if not candidates:
        return base
    return max(candidates, key=lambda p: p.stat().st_mtime)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="fftechno",
        description="Build a hardgroove techno track (ffmpeg) and a dancing-girl video.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("audio", help="stems -> mix -> master (output/techno.wav)")

    sub.add_parser("girl", help="build the B/W edge dancing-girl loop")

    vid = sub.add_parser("video", help="render + mux the dancing-girl video")
    vid.add_argument("--boost", type=float, default=1.0,
                     help="final audio gain (e.g. 2.0); 1.0 disables")
    vid.add_argument("--static", action="store_true",
                     help="render a single frozen frame (skip animation)")

    both = sub.add_parser("all", help="audio, then the girl loop, then video")
    both.add_argument("--boost", type=float, default=1.0)
    both.add_argument("--static", action="store_true",
                      help="render a single frozen frame (skip animation)")

    lvl = sub.add_parser("boost", help="re-level the existing MP4s")
    lvl.add_argument("factor", type=float, nargs="?", default=2.0,
                     help="gain factor (default 2.0)")

    sub.add_parser("synth", help="generate filters/<name>.txt from sounds.md")

    args = parser.parse_args(argv)
    from . import config as C
    from .proc import build_lock

    with build_lock(C.LOCK):
        if args.command == "audio":
            print(f"audio: {audio.build()}")
        elif args.command == "girl":
            loop, frames = _girl().build()
            print(f"girl loop: {loop}")
            print(f"girl frames: {frames}")
        elif args.command == "video":
            _girl().build()             # make sure the frame stack exists
            video.build(audio=_latest(C.AUDIO), boost=args.boost, static=args.static)
        elif args.command == "all":
            wav = audio.build()
            print(f"audio: {wav}")
            loop, _frames = _girl().build()
            print(f"girl loop: {loop}")
            video.build(audio=wav, boost=args.boost, static=args.static)
        elif args.command == "boost":
            video.re_level(args.factor, audio=_latest(C.AUDIO),
                           targets=(_latest(C.MASTER_VIDEO), _latest(C.PREVIEW_VIDEO)))
        elif args.command == "synth":
            from . import synth
            for name in synth.generate():
                print(f"wrote filters/{name}.txt")


def _girl():
    """Import the girl slice lazily (keeps onnxruntime out of audio-only runs)."""
    from . import girl
    return girl
