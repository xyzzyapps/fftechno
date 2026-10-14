"""Arrangement: parse ``song.md`` and build the mix filter graph.

The stem list and input order (Stems table), the side-chain key and low bus
(scalars), the arranged stems (Sections columns), panning (Pan rows), fixed levels
(Levels) and global effects (Effects rows) all come from markdown. Missing entries
raise. The synth graph nodes are produced separately by ``synth.py`` from templates.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


def _cells(line: str) -> list[str]:
    """Split a markdown table row on unescaped '|' (``\\|`` is a literal pipe)."""
    inner = line.strip()
    inner = inner.removeprefix("|")
    if inner.endswith("|") and not inner.endswith("\\|"):
        inner = inner[:-1]
    return [c.replace("\\|", "|").strip() for c in re.split(r"(?<!\\)\|", inner)]


@dataclass
class Song:
    """A parsed arrangement (every value originates in markdown)."""

    bpm: float
    bars: int
    fade_bars: float
    stems_order: list[str] = field(default_factory=list)
    sidechain_key: str = ""
    low_bus: list[str] = field(default_factory=list)
    arranged: list[str] = field(default_factory=list)
    boosts: dict[str, float] = field(default_factory=dict)
    sections: list[tuple[int, int, dict[str, float]]] = field(default_factory=list)
    pan: dict[str, tuple] = field(default_factory=dict)
    effects: dict[str, float] = field(default_factory=dict)
    levels: dict[str, float] = field(default_factory=dict)

    @property
    def bar_seconds(self) -> float:
        return 60.0 / self.bpm * 4.0

    @property
    def stems(self) -> set[str]:
        return set(self.stems_order)


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
        sep = (
            re.match(r"^\s*\|[\s:|.-]+\|\s*$", lines[i + 1])
            if i + 1 < len(lines)
            else None
        )
        if lines[i].lstrip().startswith("|") and sep:
            header = _cells(lines[i])
            rows: list[list[str]] = []
            j = i + 2
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                rows.append(_cells(lines[j]))
                j += 1
            tables.append((header, rows))
            i = j
        else:
            i += 1
    return tables


def parse(path: Path) -> Song:
    """Parse the ``song.md`` control surface (all values required)."""
    text = path.read_text(encoding="utf-8")
    scalars = dict(re.findall(r"^\s*([a-z_]+)\s*:\s*(\S+)\s*$", text, re.MULTILINE))
    for key in ("bpm", "bars", "fade_bars", "sidechain_key", "low_bus"):
        if key not in scalars:
            raise SystemExit(f"song.md: missing scalar '{key}'")
    song = Song(
        float(scalars["bpm"]),
        int(float(scalars["bars"])),
        float(scalars["fade_bars"]),
        sidechain_key=scalars["sidechain_key"],
        low_bus=scalars["low_bus"].split("|"),
    )

    for header, rows in _tables(text):
        head = [h.lower() for h in header]
        if head == ["stem"]:
            song.stems_order = [r[0] for r in rows]
        elif head[:2] == ["stem", "boost"]:
            song.boosts = {r[0]: float(r[1]) for r in rows}
        elif head[0] == "bars":
            cols = header[1:]
            song.arranged = list(cols)
            for row in rows:
                lo, hi = (int(x) for x in re.split(r"\s*-\s*", row[0]))
                song.sections.append(
                    (lo, hi, {cols[k]: float(row[k + 1]) for k in range(len(cols))})
                )
        elif head[:2] == ["stem", "mode"]:
            for row in rows:
                song.pan[row[0]] = (
                    ("stereo", float(row[2]), float(row[3]))
                    if row[1].strip().lower() == "stereo"
                    else (row[1].strip().lower(),)
                )
        elif head[0] == "effect":
            song.effects = {r[0]: float(r[1]) for r in rows}
        elif head[:2] == ["stem", "level"]:
            song.levels = {r[0]: float(r[1]) for r in rows}

    if not song.stems_order:
        raise SystemExit("song.md: missing Stems table")
    if not song.sections:
        raise SystemExit("song.md: missing Sections table")
    for stem in song.stems:
        _need(song.pan, stem, "Pan")
    _need(song.pan, song.sidechain_key, "Pan")
    for stem in song.low_bus:
        if stem not in song.stems:
            raise SystemExit(
                f"song.md: low_bus stem '{stem}' is not in the Stems table"
            )
    return song


def _expr(gains: list[float], starts: list[float], fade: float) -> str:
    """Nested ``if(lt(t, ...))`` automation; the last section fades to silence."""
    parts = [
        f"if(lt(t,{starts[i + 1]:.6f}),{gains[i]:g}," for i in range(len(gains) - 1)
    ]
    tail = f"{gains[-1]:g}*max(0,1-(t-{starts[-1]:.6f})/{fade:.6f})"
    return "".join(parts) + tail + ")" * len(parts)


def gain_expr(parsed: Song, stem: str) -> str:
    """The section-automation expression for *stem* (the same one the mix uses).

    The video pipeline applies this to a stem *before* the visualizer analyses it,
    so a visual follows the arrangement: a stem is silent while its section gain
    is `0.00`, while its own timing still comes from its synth graph.
    """
    if stem not in parsed.arranged:
        raise SystemExit(f"song.md: '{stem}' is not in the Sections table")
    gains = [section[2][stem] for section in parsed.sections]
    starts = [lo * parsed.bar_seconds for lo, _hi, _ in parsed.sections]
    return _expr(gains, starts, parsed.fade_bars * parsed.bar_seconds)


def _pan(stem: str, src: str, pan: dict[str, tuple]) -> str:
    placement = _need(pan, stem, "Pan")
    if placement[0] == "keep":
        # The stem is already stereo (an effect in its own graph, e.g. a ping-pong
        # delay) - pass it through instead of folding it to a point.
        return f"[{src}]acopy[{stem}]"
    if placement[0] == "center":
        return f"[{src}]pan=stereo|c0=c0|c1=c0[{stem}]"
    if placement[0] == "haas":
        return f"[{src}]pan=stereo|c0=c0|c1=c0,haas[{stem}]"
    _, left, right = placement
    return f"[{src}]pan=stereo|c0={left:g}*c0|c1={right:g}*c0[{stem}]"


def build_graph(song: Song) -> str:
    """Assemble the full mix filtergraph (a ``-/filter_complex`` file body)."""
    bar = song.bar_seconds
    index = {name: i for i, name in enumerate(song.stems_order)}
    ir_index = len(song.stems_order)
    fx = song.effects
    for key in (
        "reverb_send",
        "reverb_hpf",
        "reverb_wet",
        "sidechain_threshold",
        "sidechain_ratio",
        "sidechain_attack",
        "sidechain_release",
        "stereo_width",
        "bus_threshold",
        "bus_ratio",
        "bus_attack",
        "bus_release",
    ):
        _need(fx, key, "Effects")

    lines: list[str] = []
    starts = [lo * bar for lo, _hi, _ in song.sections]

    for stem in song.arranged:
        gains = [section[2][stem] for section in song.sections]
        boost = _need(song.boosts, stem, "Boosts")
        lines.append(
            f"[{index[stem]}]volume=volume="
            f"'{boost:g}*{_expr(gains, starts, song.fade_bars * bar)}':eval=frame[{stem}v]"
        )
        lines.append(_pan(stem, f"{stem}v", song.pan))

    for stem, level in song.levels.items():
        # A Levels stem is placed by its Pan row like any arranged stem (it used to
        # be folded to mono centre, which ignored the table).
        lines.append(f"[{index[stem]}]volume={level:g}[{stem}v]")
        lines.append(_pan(stem, f"{stem}v", song.pan))

    low = "".join(f"[{s}]" for s in song.low_bus)
    others = [s for s in song.stems_order if s not in song.low_bus]
    mixes = "".join(f"[{'keym' if s == song.sidechain_key else s}]" for s in others)
    lines += [
        f"[{song.sidechain_key}]asplit=2[keym][sckey]",
        f"{low}amix=inputs={len(song.low_bus)}:normalize=0[low]",
        f"[low][sckey]sidechaincompress=threshold={fx['sidechain_threshold']:g}"
        f":ratio={fx['sidechain_ratio']:g}:attack={fx['sidechain_attack']:g}"
        f":release={fx['sidechain_release']:g}:makeup=1[lowd]",
        f"[lowd]{mixes}amix=inputs={1 + len(others)}:normalize=0[sum]",
        "[sum]asplit=2[sm][sr]",
        f"[sr]highpass=f={fx['reverb_hpf']:g},volume={fx['reverb_send']:g}[srh]",
        f"[srh][{ir_index}]afir=dry=0:wet={fx['reverb_wet']:g}:gtype=peak[rvb]",
        f"[sm][rvb]amix=inputs=2:normalize=0,extrastereo=m={fx['stereo_width']:g},"
        f"acompressor=threshold={fx['bus_threshold']:g}:ratio={fx['bus_ratio']:g}"
        f":attack={fx['bus_attack']:g}:release={fx['bus_release']:g}[out]",
    ]
    return ";\n".join(lines) + "\n"
