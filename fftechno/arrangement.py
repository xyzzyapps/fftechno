"""Arrangement: parse ``song.md`` and build the mix filter graph.

Nothing is hard-coded: the arranged stems (Sections columns), drum patterns
(Patterns rows), fixed levels (Levels rows), panning (Pan rows) and global effects
(Effects rows) all come from ``song.md``. Missing entries raise a clear error.

Only the mix *topology* lives here: the kick side-chains a low bus, everything is
summed, a high-passed send runs through the convolution reverb, then the bus
compressor and stereo widener.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from . import config as C

STEPS_PER_BAR = 16
LOW_BUS = ("bass", "growl")      # stems ducked under the kick
KEY_STEM = "kick"                # stem that drives the side-chain


@dataclass
class Song:
    """A parsed arrangement (every value originates in song.md)."""

    bpm: float
    bars: int
    fade_bars: float
    arranged: list[str] = field(default_factory=list)
    boosts: dict[str, float] = field(default_factory=dict)
    sections: list[tuple[int, int, dict[str, float]]] = field(default_factory=list)
    pan: dict[str, tuple] = field(default_factory=dict)
    effects: dict[str, float] = field(default_factory=dict)
    patterns: dict[str, list[float]] = field(default_factory=dict)
    levels: dict[str, float] = field(default_factory=dict)

    @property
    def bar_seconds(self) -> float:
        return 60.0 / self.bpm * 4.0

    @property
    def stems(self) -> set[str]:
        return set(self.arranged) | set(self.levels)


def _need(mapping: dict, key, where: str):
    if key not in mapping:
        raise SystemExit(f"song.md: '{where}' has no entry for '{key}'")
    return mapping[key]


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


def _decode(pattern: str) -> list[float]:
    """Decode a step string ('x' hit, '1'-'9' velocity, '.'/' ' rest) to gains."""
    vals: list[float] = []
    for ch in pattern.strip():
        if ch in "xX":
            vals.append(1.0)
        elif ch.isdigit():
            vals.append(int(ch) / 9.0)
        else:
            vals.append(0.0)
    return (vals + [0.0] * STEPS_PER_BAR)[:STEPS_PER_BAR]


def parse(path: Path) -> Song:
    """Parse the ``song.md`` control surface (all values required)."""
    text = path.read_text(encoding="utf-8")
    scalars = dict(re.findall(r"^\s*([a-z_]+)\s*:\s*([0-9.]+)\s*$", text, re.M))
    for key in ("bpm", "bars", "fade_bars"):
        if key not in scalars:
            raise SystemExit(f"song.md: missing scalar '{key}'")
    song = Song(float(scalars["bpm"]), int(float(scalars["bars"])), float(scalars["fade_bars"]))

    for header, rows in _tables(text):
        head = [h.lower() for h in header]
        if head[:2] == ["stem", "boost"]:
            song.boosts = {r[0]: float(r[1]) for r in rows}
        elif head[0] == "bars":
            cols = header[1:]
            song.arranged = list(cols)
            for row in rows:
                lo, hi = (int(x) for x in re.split(r"\s*-\s*", row[0]))
                song.sections.append((lo, hi, {cols[k]: float(row[k + 1])
                                               for k in range(len(cols))}))
        elif head[:2] == ["stem", "pattern"]:
            song.patterns = {r[0]: _decode(r[1]) for r in rows}
        elif head[:2] == ["stem", "mode"]:
            for row in rows:
                song.pan[row[0]] = (("stereo", float(row[2]), float(row[3]))
                                    if row[1].strip().lower() == "stereo" else (row[1].strip().lower(),))
        elif head[0] == "effect":
            song.effects = {r[0]: float(r[1]) for r in rows}
        elif head[:2] == ["stem", "level"]:
            song.levels = {r[0]: float(r[1]) for r in rows}

    if not song.sections:
        raise SystemExit("song.md: missing Sections table")
    for stem in song.stems:
        _need(song.pan, stem, "Pan")
    return song


def _expr(gains: list[float], starts: list[float], fade: float) -> str:
    """Nested ``if(lt(t, ...))`` automation; the last section fades to silence."""
    parts = [f"if(lt(t,{starts[i + 1]:.6f}),{gains[i]:g}," for i in range(len(gains) - 1)]
    tail = f"{gains[-1]:g}*max(0,1-(t-{starts[-1]:.6f})/{fade:.6f})"
    return "".join(parts) + tail + ")" * len(parts)


def _gate(vals: list[float], bar: float, step: float) -> str:
    """Per-step gate: velocity of the current 16th, 0 on a rest."""
    key = f"floor(mod(t,{bar:.6f})/{step:.6f})"
    parts = [f"if(eq({key},{s}),{v:g}," for s, v in enumerate(vals)]
    return "".join(parts) + "0" + ")" * len(parts)


def _pan(stem: str, src: str, pan: dict[str, tuple]) -> str:
    placement = _need(pan, stem, "Pan")
    if placement[0] == "center":
        return f"[{src}]pan=stereo|c0=c0|c1=c0[{stem}]"
    if placement[0] == "haas":
        return f"[{src}]pan=stereo|c0=c0|c1=c0,haas[{stem}]"
    _, left, right = placement
    return f"[{src}]pan=stereo|c0={left:g}*c0|c1={right:g}*c0[{stem}]"


def build_graph(song: Song) -> str:
    """Assemble the full mix filtergraph (a ``-filter_complex_script`` body)."""
    bar = song.bar_seconds
    step = bar / STEPS_PER_BAR
    index = {name: i for i, name in enumerate(C.MIX_INPUTS)}
    ir_index = len(C.MIX_INPUTS)
    fx = song.effects
    for key in ("reverb_send", "reverb_hpf", "reverb_wet", "sidechain_threshold",
                "sidechain_ratio", "sidechain_attack", "sidechain_release",
                "stereo_width", "bus_threshold", "bus_ratio", "bus_attack", "bus_release"):
        _need(fx, key, "Effects")

    lines: list[str] = []
    starts = [lo * bar for lo, _hi, _ in song.sections]

    for stem in song.arranged:
        gains = [section[2][stem] for section in song.sections]
        boost = _need(song.boosts, stem, "Boosts")
        lines.append(f"[{index[stem]}]volume=volume="
                     f"'{boost:g}*{_expr(gains, starts, song.fade_bars * bar)}':eval=frame[{stem}v]")
        src = f"{stem}v"
        if stem in song.patterns:
            lines.append(f"[{src}]aeval=exprs='val(0)*{_gate(song.patterns[stem], bar, step)}'[{stem}g]")
            src = f"{stem}g"
        lines.append(_pan(stem, src, song.pan))

    for stem, level in song.levels.items():
        lines.append(f"[{index[stem]}]volume={level:g},pan=stereo|c0=0.5*c0|c1=0.5*c0[{stem}]")

    low = "".join(f"[{s}]" for s in LOW_BUS)
    others = "".join(f"[{('kickm' if s == KEY_STEM else s)}]"
                     for s in C.MIX_INPUTS if s in song.stems and s not in LOW_BUS)
    count = 1 + len([s for s in C.MIX_INPUTS if s in song.stems and s not in LOW_BUS])
    lines += [
        f"[{KEY_STEM}]asplit=2[kickm][key]",
        f"{low}amix=inputs={len(LOW_BUS)}:normalize=0[low]",
        f"[low][key]sidechaincompress=threshold={fx['sidechain_threshold']:g}"
        f":ratio={fx['sidechain_ratio']:g}:attack={fx['sidechain_attack']:g}"
        f":release={fx['sidechain_release']:g}:makeup=1[lowd]",
        f"[lowd]{others}amix=inputs={count}:normalize=0[sum]",
        "[sum]asplit=2[sm][sr]",
        f"[sr]highpass=f={fx['reverb_hpf']:g},volume={fx['reverb_send']:g}[srh]",
        f"[srh][{ir_index}]afir=dry=0:wet={fx['reverb_wet']:g}:gtype=peak[rvb]",
        f"[sm][rvb]amix=inputs=2:normalize=0,extrastereo=m={fx['stereo_width']:g},"
        f"acompressor=threshold={fx['bus_threshold']:g}:ratio={fx['bus_ratio']:g}"
        f":attack={fx['bus_attack']:g}:release={fx['bus_release']:g}[out]",
    ]
    return ";\n".join(lines) + "\n"
