"""Arrangement: parse ``song.md`` and build the mix filter graph.

Per-stem section gains live in ``song.md`` as a markdown table; this module turns
them into ffmpeg ``volume=...:eval=frame`` automation and assembles the full mix
graph (panning, kick side-chain, reverb bus).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from . import config as C

# Stems whose level is programmed per section in song.md.
AUTO_STEMS = ("kick", "clap", "hat", "ohat", "perc", "shaker",
              "bongo", "rim", "bass", "growl", "acid")

# Stems with a fixed level (their content is placed by their own graphs).
CONST_STEMS: dict[str, float] = {"vox": 1.0, "beeps": 1.0}

# Stereo placement: "center", "center_haas", or (left, right) gains.
PAN: dict[str, object] = {
    "kick": "center", "clap": "center", "bass": "center",
    "hat": (0.62, 0.38), "ohat": (0.38, 0.62),
    "acid": (0.42, 0.58), "shaker": (0.35, 0.65),
    "growl": (0.58, 0.42), "bongo": (0.42, 0.58), "rim": (0.62, 0.38),
    "perc": "center_haas", "vox": "center", "beeps": "center",
}


@dataclass
class Song:
    """A parsed arrangement."""

    bpm: float
    bars: int
    fade_bars: float
    boosts: dict[str, float]
    sections: list[tuple[int, int, dict[str, float]]]   # (bar_start, bar_end, gains)

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
            rows = []
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
    """Parse a ``song.md`` arrangement file."""
    text = path.read_text(encoding="utf-8")
    scalars = dict(re.findall(r"^\s*([a-z_]+)\s*:\s*([0-9.]+)\s*$", text, re.M))
    bpm = float(scalars.get("bpm", C.BPM))
    bars = int(float(scalars["bars"])) if "bars" in scalars else 140
    fade_bars = float(scalars.get("fade_bars", 0.0))

    boosts: dict[str, float] = {}
    sections: list[tuple[int, int, dict[str, float]]] = []
    for header, rows in _tables(text):
        head = [h.lower() for h in header]
        if head[:2] == ["stem", "boost"]:
            boosts = {row[0]: float(row[1]) for row in rows}
        elif head[0] == "bars":
            cols = header[1:]
            for row in rows:
                lo, hi = (int(x) for x in re.split(r"\s*-\s*", row[0]))
                gains = {cols[k]: float(row[k + 1]) for k in range(len(cols))}
                sections.append((lo, hi, gains))
    if not sections:
        raise ValueError(f"no sections table found in {path}")
    return Song(bpm, bars, fade_bars, boosts, sections)


def _expr(gains: list[float], starts: list[float], fade: float) -> str:
    """Nested ``if(lt(t, ...))`` automation; the last section fades to silence."""
    parts = [f"if(lt(t,{starts[i + 1]:.6f}),{gains[i]:g}," for i in range(len(gains) - 1)]
    tail = f"{gains[-1]:g}*max(0,1-(t-{starts[-1]:.6f})/{fade:.6f})"
    return "".join(parts) + tail + ")" * len(parts)


def _pan(stem: str, src: str) -> str:
    placement = PAN.get(stem, "center")
    if placement == "center":
        return f"[{src}]pan=stereo|c0=c0|c1=c0[{stem}]"
    if placement == "center_haas":
        return f"[{src}]pan=stereo|c0=c0|c1=c0,haas[{stem}]"
    left, right = placement            # type: ignore[misc]
    return f"[{src}]pan=stereo|c0={left}*c0|c1={right}*c0[{stem}]"


def build_graph(song: Song) -> str:
    """Assemble the full mix filtergraph (a ``-filter_complex_script`` body)."""
    bar = song.bar_seconds
    index = {name: i for i, name in enumerate(C.MIX_INPUTS)}
    ir_index = len(C.MIX_INPUTS)

    lines: list[str] = []
    starts = [lo * bar for lo, _hi, _ in song.sections]

    for stem in AUTO_STEMS:
        gains = [section[2][stem] for section in song.sections]
        boost = song.boosts.get(stem, 1.0)
        expr = _expr(gains, starts, song.fade_bars * bar)
        lines.append(f"[{index[stem]}]volume=volume='{boost:g}*{expr}':eval=frame[{stem}v]")
        lines.append(_pan(stem, f"{stem}v"))

    for stem, level in CONST_STEMS.items():
        lines.append(f"[{index[stem]}]volume={level:g},pan=stereo|c0=0.5*c0|c1=0.5*c0[{stem}]")

    lines += [
        "[kick]asplit=2[kickm][key]",
        "[bass][growl]amix=inputs=2:normalize=0[low]",
        "[low][key]sidechaincompress=threshold=0.03:ratio=12:attack=5:release=120:makeup=1[lowd]",
        "[lowd][clap][hat][ohat][perc][kickm][acid][shaker][vox][bongo][rim][beeps]"
        "amix=inputs=12:normalize=0[sum]",
        "[sum]asplit=2[sm][sr]",
        "[sr]highpass=f=300,volume=0.7[srh]",
        f"[srh][{ir_index}]afir=dry=0:wet=1:gtype=peak[rvb]",
        "[sm][rvb]amix=inputs=2:normalize=0,extrastereo=m=1.3,"
        "acompressor=threshold=0.1:ratio=3:attack=10:release=150[out]",
    ]
    return ";\n".join(lines) + "\n"
