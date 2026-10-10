"""Command line entry point for the fftechno build."""

from __future__ import annotations

import argparse

from . import audio, video

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="fftechno",
        description="Build a hardgroove techno track (ffmpeg) and an ASCII video.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("audio", help="stems -> mix -> master (output/techno.wav)")

    vid = sub.add_parser("video", help="render + mux the ASCII video")
    vid.add_argument("--boost", type=float, default=1.0,
                     help="final audio gain (e.g. 2.0); 1.0 disables")
    vid.add_argument("--static", action="store_true",
                     help="render a single frozen frame (skip animation)")

    both = sub.add_parser("all", help="audio, then video")
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
            audio.build()
        elif args.command == "video":
            video.build(boost=args.boost, static=args.static)
        elif args.command == "all":
            audio.build()
            video.build(boost=args.boost, static=args.static)
        elif args.command == "boost":
            video.re_level(args.factor)
        elif args.command == "synth":
            from . import synth
            for name in synth.generate():
                print(f"wrote filters/{name}.txt")
