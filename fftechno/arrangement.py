"""Arrangement: parse ``song.md`` and build the mix filter graph.

``song.md`` is the single control surface: per-stem section gains, per-stem pan,
and global effect parameters (side-chain, reverb bus, stereo width, bus comp).
This module turns it into an ffmpeg filtergraph.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from . import config as C

# Stems whose level is programmed per section in song.md.
AUTO_STEMS = ("kick", "clap", "hat", "ohat", "perc", "shaker",
              "bongo", "rim", "bass", "growl", "acid")

# Stems with a fixed level (their content is placed by their own graphs).
CONST_STEMS: dict[str, float] = {"vox": 1.0, "beeps": 1.0}

# Default stereo placement per stem: ("center" | "haas" | ("stereo", left, right)).
DEFAULT_PAN: dict[str, tuple] = {
    "kick": ("center",), "clap": ("center",), "bass": ("center",),
    "hat": ("stereo", 0.62, 0.38), "ohat": ("stereo", 0.38, 0.62),
    "acid": ("stereo", 0.42, 0.58), "shaker": ("stereo", 0.35, 0.65),
    "growl": ("stereo", 0.58, 0.42), "bongo": ("stereo", 0.42, 0.58),
    "rim": ("stereo", 0.62, 0.38), "perc": ("haas",),
    "vox": ("center",), "beeps": ("center",),
}

# Default global effect parameters (overridable from the Effects table).
DEFAULT_EFFECTS: dict[str, float] = {
    "reverb_send": 0.7, "reverb_hpf": 300, "reverb_wet": 1.0,
    "sidechain_threshold": 0.03, "sidechain_ratio": 12,
    "sidechain_attack": 5, "sidechain_release": 120,
    "stereo_width": 1.3,
    "bus_threshold": 0.1, "bus_ratio": 3, "bus_attack": 10, "bus_release": 150,
}


@dataclass
class Song:
    """A parsed arrangement."""

    bpm: float
    bars: int
    fade_bars: float
    boosts: dict[str, float] = field(default_factory=dict)
    sections: list[tuple[int, int, dict[str, float]]] = field(default_factory=list)
    pan: dict[str, tuple] = field(default_factory=dict)
    effects: dict[str, float] = field(default_factory=dict)

    @property
    def bar_seconds(self) -> float:
        return 60.0 / self.bpm * 4.0


def _tables(text: str) -> list[tuple[list[str], list[list[str]]]]:
    """Return (header, rows) for every markdown table in *text*."""
    tables: list[tuple[list[str], list[list[str]]]] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        sep = re.match(r"^\s*\|[\s:|.-]+\|\s*$", lines[i + 1]) if i + 1 < len(lines) else None
        if lines[i].lstrip().startswith("|") and sep:
            header = [c.strip() for c in lines[i].strip().strip("|").split("|")]
            rows: list[list[str]] = []
            j = i + 2
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                rows.append([c.strip() for c in lines[j].strip().strip("|").split("|")])
                j += 1
            tables.append((header, rows))
            i = j
        else:
            i += 1
    return tables


def parse(path: Path) -> Song:
    """Parse the ``song.md`` control surface."""
    text = path.read_text(encoding="utf-8")
    scalars = dict(re.findall(r"^\s*([a-z_]+)\s*:\s*([0-9.]+)\s*$", text, re.M))
    bpm = float(scalars.get("bpm", C.BPM))
    bars = int(float(scalars["bars"])) if "bars" in scalars else 140
    fade_bars = float(scalars.get("fade_bars", 0.0))

    song = Song(bpm, bars, fade_bars)
    for header, rows in _tables(text):
        head = [h.lower() for h in header]
        if head[:2] == ["stem", "boost"]:
            song.boosts = {row[0]: float(row[1]) for row in rows}
        elif head[0] == "bars":
            cols = header[1:]
            for row in rows:
                lo, hi = (int(x) for x in re.split(r"\s*-\s*", row[0]))
                gains = {cols[k]: float(row[k + 1]) for k in range(len(cols))}
                song.sections.append((lo, hi, gains))
        elif head[:2] == ["stem", "mode"]:
            for row in rows:
                mode = row[1].strip().lower()
                if mode == "stereo":
                    song.pan[row[0]] = ("stereo", float(row[2]), float(row[3]))
                else:
                    song.pan[row[0]] = (mode,)
        elif head[0] == "effect":
            song.effects = {row[0]: float(row[1]) for row in rows}
    if not song.sections:
        raise ValueError(f"no sections table found in {path}")
    return song


def _expr(gains: list[float], starts: list[float], fade: float) -> str:
    """Nested ``if(lt(t, ...))`` automation; the last section fades to silence."""
    parts = [f"if(lt(t,{starts[i + 1]:.6f}),{gains[i]:g}," for i in range(len(gains) - 1)]
    tail = f"{gains[-1]:g}*max(0,1-(t-{starts[-1]:.6f})/{fade:.6f})"
    return "".join(parts) + tail + ")" * len(parts)


def _pan(stem: str, src: str, pan: dict[str, tuple]) -> str:
    placement = pan.get(stem, DEFAULT_PAN.get(stem, ("center",)))
    if placement[0] == "center":
        return f"[{src}]pan=stereo|c0=c0|c1=c0[{stem}]"
    if placement[0] == "haas":
        return f"[{src}]pan=stereo|c0=c0|c1=c0,haas[{stem}]"
    _, left, right = placement
    return f"[{src}]pan=stereo|c0={left:g}*c0|c1={right:g}*c0[{stem}]"


def build_graph(song: Song) -> str:
    """Assemble the full mix filtergraph (a ``-filter_complex_script`` body)."""
    bar = song.bar_seconds
    index = {name: i for i, name in enumerate(C.MIX_INPUTS)}
    ir_index = len(C.MIX_INPUTS)
    fx = {**DEFAULT_EFFECTS, **song.effects}

    lines: list[str] = []
    starts = [lo * bar for lo, _hi, _ in song.sections]

    for stem in AUTO_STEMS:
        gains = [section[2][stem] for section in song.sections]
        boost = song.boosts.get(stem, 1.0)
        expr = _expr(gains, starts, song.fade_bars * bar)
        lines.append(f"[{index[stem]}]volume=volume='{boost:g}*{expr}':eval=frame[{stem}v]")
        lines.append(_pan(stem, f"{stem}v", song.pan))

    for stem, level in CONST_STEMS.items():
        lines.append(f"[{index[stem]}]volume={level:g},pan=stereo|c0=0.5*c0|c1=0.5*c0[{stem}]")

    lines += [
        "[kick]asplit=2[kickm][key]",
        "[bass][growl]amix=inputs=2:normalize=0[low]",
        f"[low][key]sidechaincompress=threshold={fx['sidechain_threshold']:g}"
        f":ratio={fx['sidechain_ratio']:g}:attack={fx['sidechain_attack']:g}"
        f":release={fx['sidechain_release']:g}:makeup=1[lowd]",
        "[lowd][clap][hat][ohat][perc][kickm][acid][shaker][vox][bongo][rim][beeps]"
        "amix=inputs=12:normalize=0[sum]",
        "[sum]asplit=2[sm][sr]",
        f"[sr]highpass=f={fx['reverb_hpf']:g},volume={fx['reverb_send']:g}[srh]",
        f"[srh][{ir_index}]afir=dry=0:wet={fx['reverb_wet']:g}:gtype=peak[rvb]",
        f"[sm][rvb]amix=inputs=2:normalize=0,extrastereo=m={fx['stereo_width']:g},"
        f"acompressor=threshold={fx['bus_threshold']:g}:ratio={fx['bus_ratio']:g}"
        f":attack={fx['bus_attack']:g}:release={fx['bus_release']:g}[out]",
    ]
    return ";\n".join(lines) + "\n"
