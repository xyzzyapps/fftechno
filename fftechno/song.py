"""A song is a folder under ``songs/<name>/``.

``song.md`` is the arrangement, ``sounds.md`` the instruments, ``vocals.md`` the
TTS lines and ``video.md`` the picture. Adding a song is adding that folder.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from . import config as C
from .md import rows as _rows
from .md import scalars as _scalars


# ---------------------------------------------------------------------------
# Song data
# ---------------------------------------------------------------------------
@dataclass
class Vocals:
    """TTS voice and the (text, time) phrase list."""

    engine: str = "kitten"
    voice: str = "Luna"
    trim_lead: bool = False  # cut the TTS's leading silence before placing
    lines: list[tuple[str, float]] = field(default_factory=list)


@dataclass
class Video:
    """The song's visual: source clip, crop window, default look and loop length."""

    source: str = ""  # relative to the project root, or absolute
    crop_start: float = 2.0
    crop_duration: float = 3.0
    look: str = "outline"
    loop_beats: int | None = None
    effects: list[str] = field(default_factory=list)  # effect chain (video.md)
    width: int = 1920  # output size (video.md `size: WxH`), e.g. 1080x1920 vertical
    height: int = 1080
    params: dict[tuple[str, str], str] = field(default_factory=dict)

    @property
    def half(self) -> tuple[int, int]:
        """The picture-data frame (half the output), as ``(width, height)``."""
        return (self.width // 2, self.height // 2)

    @property
    def preview(self) -> tuple[int, int]:
        """A 720p-class preview size for this aspect, as ``(width, height)``."""
        return (1280, 720) if self.width >= self.height else (720, 1280)

    def source_path(self) -> Path:
        p = Path(self.source) if self.source else Path("")
        return p if p.is_absolute() else (C.ROOT / p)


class Song:
    """A track: its markdown files, derived timing and output paths."""

    def __init__(self, name: str) -> None:
        if not name:
            raise ValueError("a Song needs a name")
        self.name = name

    # --- paths -------------------------------------------------------------
    @property
    def dir(self) -> Path:
        return C.SONGS / self.name

    @property
    def song_md(self) -> Path:
        return self.dir / "song.md"

    @property
    def sounds_md(self) -> Path:
        return self.dir / "sounds.md"

    @property
    def vocals_md(self) -> Path:
        return self.dir / "vocals.md"

    @property
    def video_md(self) -> Path:
        return self.dir / "video.md"

    @property
    def filters(self) -> Path:
        return C.FILTERS / self.name

    @property
    def output(self) -> Path:
        return C.OUTPUT / self.name

    @property
    def stems(self) -> Path:
        return self.output / "stems"

    @property
    def logs(self) -> Path:
        return self.output / "logs"

    @property
    def audio(self) -> Path:
        return self.output / "techno.wav"

    @property
    def mix_pre(self) -> Path:
        return self.output / "mix_pre.wav"

    @property
    def ir(self) -> Path:
        return self.logs / "ir.wav"

    @property
    def lock(self) -> Path:
        return self.logs / ".build.lock"

    @property
    def master_video(self) -> Path:
        return self.output / "techno_visualizer.mp4"

    @property
    def preview_video(self) -> Path:
        return self.output / "techno_visualizer_720p.mp4"

    @property
    def girl_loop(self) -> Path:
        return self.output / "girl_loop.mp4"

    @property
    def girl_frames(self) -> Path:
        return self.output / "girl_frames.npy"

    @property
    def girl_sprites(self) -> Path:
        return self.output / "girl_sprites.npy"

    @property
    def girl_pick(self) -> Path:
        return self.output / "girl_pick.npy"

    @property
    def lyrics(self) -> Path:
        return self.output / "lyrics.json"

    # --- music -------------------------------------------------------------
    def arrangement(self):
        """Parse ``song.md`` (cached)."""
        if getattr(self, "_arr", None) is None:
            from . import arrangement

            self._arr = arrangement.parse(self.song_md)
        return self._arr

    @property
    def bpm(self) -> float:
        return self.arrangement().bpm

    @property
    def bar(self) -> float:
        return 60.0 / self.bpm * 4.0

    @property
    def duration(self) -> float:
        return self.arrangement().bars * self.bar

    # --- vocals ------------------------------------------------------------
    def vocals(self) -> Vocals:
        if not self.vocals_md.exists():
            return Vocals()
        text = self.vocals_md.read_text(encoding="utf-8")
        scalars = _scalars(text)
        lines = [(r[0], float(r[1])) for r in _rows(text, ["text", "time"])]
        return Vocals(
            engine=scalars.get("engine", "kitten"),
            voice=scalars.get("voice", "Luna"),
            trim_lead=scalars.get("trim_lead", "0").lower() not in ("0", "false", "no"),
            lines=lines,
        )

    # --- video -------------------------------------------------------------
    def video(self) -> Video:
        if not self.video_md.exists():
            return Video()
        text = self.video_md.read_text(encoding="utf-8")
        scalars = _scalars(text)
        params = {}
        # The parameters table is keyed by look *or* effect name (both live here).
        for row in _rows(text, ["look", "key", "value"]) or _rows(
            text, ["name", "key", "value"]
        ):
            params[(row[0], row[1])] = row[2]
        loop = scalars.get("loop_beats")
        width, height = C.VIDEO_W, C.VIDEO_H
        size = scalars.get("size", "")
        if size:
            match = re.fullmatch(r"(\d+)[xX](\d+)", size)
            if not match:
                raise SystemExit(f"video.md: 'size' must be WxH (got '{size}')")
            width, height = int(match.group(1)), int(match.group(2))
        # The effect chain is a comma list and, unlike other scalars, may contain
        # spaces (`effects: squares, grain`), so read it with its own pattern.
        chain = re.search(r"^\s*effects\s*:\s*(.+?)\s*$", text, re.MULTILINE)
        return Video(
            source=scalars.get("source", ""),
            crop_start=float(scalars.get("crop_start", 2.0)),
            crop_duration=float(scalars.get("crop_duration", 3.0)),
            look=scalars.get("look", "outline"),
            loop_beats=int(loop) if loop else None,
            effects=(
                [e.strip() for e in chain.group(1).split(",") if e.strip()]
                if chain
                else []
            ),
            width=width,
            height=height,
            params=params,
        )


def names() -> list[str]:
    """Song names: the folder names under ``songs/``."""
    if not C.SONGS.exists():
        return []
    return sorted(p.name for p in C.SONGS.iterdir() if p.is_dir())


def load(name: str) -> Song:
    """Return the song for *name*."""
    if name not in names():
        raise SystemExit(
            f"unknown song '{name}' (have: {', '.join(names()) or 'none'})"
        )
    return Song(name)
