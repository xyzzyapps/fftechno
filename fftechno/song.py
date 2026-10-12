"""Songs: an abstract :class:`Song` plus one thin subclass per track.

All song-specific *data* lives in ``songs/<name>/`` - ``song.md`` (arrangement),
``sounds.md`` (instruments), ``vocals.md`` (TTS voice + phrase times) and
``video.md`` (source clip, crop, look). The code below is generic: the subclasses
only set ``name``, and every value is read from the folder, so adding a song is a
matter of adding a folder (and, optionally, a subclass).
"""

from __future__ import annotations

import re
from abc import ABC
from dataclasses import dataclass, field
from pathlib import Path

from . import config as C


# ---------------------------------------------------------------------------
# Tiny markdown readers (shared with the style of song.md / sounds.md)
# ---------------------------------------------------------------------------
def _cells(line: str) -> list[str]:
    inner = line.strip()
    inner = inner.removeprefix("|")
    if inner.endswith("|") and not inner.endswith("\\|"):
        inner = inner[:-1]
    return [c.replace("\\|", "|").strip() for c in re.split(r"(?<!\\)\|", inner)]


def _scalars(text: str) -> dict[str, str]:
    return {
        m.group(1): m.group(2)
        for m in re.finditer(r"^\s*([a-z_]+)\s*:\s*(\S+)\s*$", text, re.MULTILINE)
    }


def _rows(text: str, header: list[str]) -> list[list[str]]:
    """Rows of the first table whose header matches *header* (case-insensitive)."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if i + 1 >= len(lines) or not line.lstrip().startswith("|"):
            continue
        if not re.match(r"^\s*\|[\s:|.-]+\|\s*$", lines[i + 1]):
            continue
        if [c.lower() for c in _cells(line)] == header:
            rows = []
            j = i + 2
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                rows.append(_cells(lines[j]))
                j += 1
            return rows
    return []


# ---------------------------------------------------------------------------
# Song data
# ---------------------------------------------------------------------------
@dataclass
class Vocals:
    """TTS voice and the (text, time) phrase list."""

    engine: str = "kitten"
    voice: str = "Luna"
    lines: list[tuple[str, float]] = field(default_factory=list)


@dataclass
class Video:
    """The song's visual: source clip, crop window, default look and loop length."""

    source: str = ""  # relative to the project root, or absolute
    crop_start: float = 2.0
    crop_duration: float = 3.0
    look: str = "outline"
    loop_beats: int | None = None
    params: dict[tuple[str, str], str] = field(default_factory=dict)

    def source_path(self) -> Path:
        p = Path(self.source) if self.source else Path("")
        return p if p.is_absolute() else (C.ROOT / p)

    def look_param(self, look: str, key: str, default):
        raw = self.params.get((look, key))
        if raw is None:
            return default
        return type(default)(raw) if default is not None else raw


class Song(ABC):
    """A track: its four markdown files, derived timing and output paths."""

    name: str = ""

    def __init__(self, name: str | None = None) -> None:
        if name:
            self.name = name
        if not self.name:
            raise ValueError("a Song needs a name")

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
            lines=lines,
        )

    # --- video -------------------------------------------------------------
    def video(self) -> Video:
        if not self.video_md.exists():
            return Video()
        text = self.video_md.read_text(encoding="utf-8")
        scalars = _scalars(text)
        params = {}
        for row in _rows(text, ["look", "key", "value"]):
            params[(row[0], row[1])] = row[2]
        loop = scalars.get("loop_beats")
        return Video(
            source=scalars.get("source", ""),
            crop_start=float(scalars.get("crop_start", 2.0)),
            crop_duration=float(scalars.get("crop_duration", 3.0)),
            look=scalars.get("look", "outline"),
            loop_beats=int(loop) if loop else None,
            params=params,
        )


class _GenericSong(Song):
    """Used when a ``songs/<name>/`` folder has no registered subclass."""


SONGS: dict[str, type[Song]] = {}


def register(cls: type[Song]) -> type[Song]:
    """Decorator: add a Song subclass to the registry."""
    SONGS[cls.name] = cls
    return cls


@register
class Basement(Song):
    name = "basement"


@register
class Hardgroove(Song):
    name = "hardgroove"


def names() -> list[str]:
    """All song names (folders on disk, plus any registered but missing a folder)."""
    found = (
        {p.name for p in C.SONGS.iterdir() if p.is_dir()} if C.SONGS.exists() else set()
    )
    return sorted(found | set(SONGS))


def load(name: str) -> Song:
    """Return the Song for *name* (a registered subclass, or a generic one)."""
    if name not in names():
        raise SystemExit(
            f"unknown song '{name}' (have: {', '.join(names()) or 'none'})"
        )
    return SONGS.get(name, _GenericSong)(name)
