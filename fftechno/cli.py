"""Command line entry point for the fftechno build."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from . import audio, video
from . import song as songs


def _latest(base: Path) -> Path:
    """Newest existing file matching *base* or its ``_vN`` versions.

    The match is anchored, so a stem that is a prefix of another file's name cannot
    pick it up by mistake (`techno_visualizer.mp4` must not match
    `techno_visualizer_720p.mp4`).
    """
    name = re.compile(rf"{re.escape(base.stem)}(_v\d+)?{re.escape(base.suffix)}")
    candidates = [
        p
        for p in base.parent.glob(f"{base.stem}*{base.suffix}")
        if name.fullmatch(p.name)
    ]
    if not candidates:
        return base
    return max(candidates, key=lambda p: p.stat().st_mtime)


def _girl():
    """Import the girl slice lazily (keeps onnxruntime out of audio-only runs)."""
    from . import girl

    return girl


def _add_song(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--song",
        default=songs.names()[0] if songs.names() else "basement",
        help="which song under songs/ (default: %(default)s)",
    )


def _add_look(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--look",
        choices=("edge", "pollock", "outline", "photo"),
        default=None,
        help="picture source (default: the song's video.md)",
    )
    parser.add_argument(
        "--mode",
        choices=("reset", "trail", "build"),
        default=None,
        help="Pollock paint accumulation (default: the look's)",
    )


def _add_fx(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--fx",
        default=None,
        help="comma-separated effect chain, e.g. 'squares,grain' "
        "(default: the song's video.md, else the built-in chain)",
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="fftechno",
        description="Build a techno track (ffmpeg) and a dancing-girl video.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    aud = sub.add_parser(
        "audio", help="stems -> mix -> master (output/<song>/techno.wav)"
    )
    _add_song(aud)
    aud.add_argument(
        "--safe",
        action="store_true",
        help="apply the extra ear-protection limiter (off by default)",
    )
    aud.add_argument(
        "--tts",
        choices=("kitten", "piper", "flite"),
        default=None,
        help="vocal TTS engine (default: the song's vocals.md)",
    )

    girl = sub.add_parser("girl", help="build the dancing-girl loop")
    _add_song(girl)
    _add_look(girl)

    vid = sub.add_parser("video", help="render + mux the video")
    _add_song(vid)
    _add_look(vid)
    _add_fx(vid)
    vid.add_argument(
        "--boost",
        type=float,
        default=1.0,
        help="final audio gain (e.g. 2.0); 1.0 disables",
    )
    vid.add_argument(
        "--static",
        action="store_true",
        help="render a single frozen frame (skip animation)",
    )

    both = sub.add_parser("all", help="audio, then the girl loop, then video")
    _add_song(both)
    _add_look(both)
    _add_fx(both)
    both.add_argument(
        "--safe", action="store_true", help="apply the ear-protection limiter"
    )
    both.add_argument(
        "--tts",
        choices=("kitten", "piper", "flite"),
        default=None,
        help="vocal TTS engine (default: the song's vocals.md)",
    )
    both.add_argument("--boost", type=float, default=1.0)
    both.add_argument(
        "--static",
        action="store_true",
        help="render a single frozen frame (skip animation)",
    )

    lvl = sub.add_parser("boost", help="re-level the existing MP4s")
    _add_song(lvl)
    lvl.add_argument(
        "factor", type=float, nargs="?", default=2.0, help="gain factor (default 2.0)"
    )

    swp = sub.add_parser(
        "swap", help="swap in the current master audio (video copied, no re-render)"
    )
    _add_song(swp)

    syn = sub.add_parser(
        "synth", help="generate filters/<song>/<name>.txt from sounds.md"
    )
    _add_song(syn)

    args = parser.parse_args(argv)
    from .proc import build_lock

    song = songs.load(args.song)
    with build_lock(song.lock):
        if args.command == "audio":
            print(f"audio: {audio.build(song, safe=args.safe, tts=args.tts)}")
        elif args.command == "girl":
            loop, data = _girl().build(song, look=args.look, mode=args.mode)
            print(f"girl loop: {loop}")
            print(f"girl data: {data}")
        elif args.command == "video":
            _girl().build(song, look=args.look, mode=args.mode)  # ensure the picture
            video.build(
                song,
                audio=_latest(song.audio),
                look=args.look,
                mode=args.mode,
                boost=args.boost,
                static=args.static,
                fx_chain=args.fx,
            )
        elif args.command == "all":
            wav = audio.build(song, safe=args.safe, tts=args.tts)
            print(f"audio: {wav}")
            loop, _data = _girl().build(song, look=args.look, mode=args.mode)
            print(f"girl loop: {loop}")
            video.build(
                song,
                audio=wav,
                look=args.look,
                mode=args.mode,
                boost=args.boost,
                static=args.static,
                fx_chain=args.fx,
            )
        elif args.command == "boost":
            video.re_level(
                args.factor,
                song,
                audio=_latest(song.audio),
                targets=(_latest(song.master_video), _latest(song.preview_video)),
            )
        elif args.command == "swap":
            video.swap_audio(
                song,
                audio=_latest(song.audio),
                targets=(_latest(song.master_video), _latest(song.preview_video)),
            )
        elif args.command == "synth":
            from . import synth

            for name in synth.generate(song):
                print(f"wrote filters/{song.name}/{name}.txt")
