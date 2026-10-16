"""Markdown-driven synthesis.

``sounds.md`` defines instruments (``name | template | parameters``) and global
scalars; ``templates/*.txt`` are ffmpeg filtergraphs with placeholders, rendered to
``filters/<name>.txt`` by ``python -m fftechno synth``. There are no defaults -
every placeholder must be supplied, otherwise generation fails loudly.

``bar``, ``step``, ``beat`` and ``dur`` are not written in ``sounds.md``. They are
computed from ``song.md`` (``bpm`` and ``bars``) and may be referenced as
``{{bar}}``, ``{{step}}`` and ``{{beat}}`` inside other scalars.

Template language
-----------------
``{{ key }}``                    value substitution
``{{ if_steps(SEQ; GRID; DEF) }}``  expand a comma list into a nested
                                 ``if(eq(GRID,0),v0, ... ,DEF)`` - used to build
                                 per-step melodies/patterns from markdown.
"""

from __future__ import annotations

import re

from . import config as C
from .md import rows, scalars

_PLACEHOLDER = re.compile(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}")
_IF_STEPS = re.compile(r"\{\{\s*if_steps\(([^}]*)\)\s*\}\}")
# These four come from song.md. A sounds.md copy would drift from the arrangement.
_CLOCKS = ("bar", "step", "beat", "dur")


def _num(value: float) -> str:
    """A decimal ffmpeg can parse, with enough digits that a bar stays on the grid."""
    return f"{value:.12f}".rstrip("0").rstrip(".")


def _clocks(song) -> dict[str, str]:
    """Timing tokens derived from ``song.md``."""
    bpm = song.bpm
    beat = 60.0 / bpm
    bar = beat * 4.0
    return {
        "beat": _num(beat),
        "bar": _num(bar),
        "step": _num(beat / 4.0),
        "dur": _num(song.duration),
    }


def _expand(values: dict[str, str], name: str) -> dict[str, str]:
    """Replace ``{{key}}`` inside scalar values (clocks referenced by other clocks)."""
    out = dict(values)
    for _ in range(16):
        changed = False
        for key, raw in list(out.items()):

            def repl(match: re.Match[str], current: dict[str, str] = out) -> str:
                token = match.group(1)
                if token not in current:
                    return match.group(0)
                return current[token]

            new = _PLACEHOLDER.sub(repl, raw)
            if new != raw:
                changed = True
                out[key] = new
        if not changed:
            return out
    raise SystemExit(f"sounds.md: '{name}' placeholders did not settle")


def _params(cell: str) -> dict[str, str]:
    """Parse a ``key=value, key=value`` parameter cell."""
    out: dict[str, str] = {}
    for part in cell.split(","):
        if "=" in part:
            key, value = part.split("=", 1)
            out[key.strip()] = value.strip()
    return out


def _simple(text: str, values: dict[str, str], name: str) -> str:
    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in values:
            raise SystemExit(f"sounds.md: instrument '{name}' needs value '{key}'")
        return values[key]

    return _PLACEHOLDER.sub(repl, text)


def _val(values: dict[str, str], token: str, name: str) -> str:
    """Resolve an ``if_steps`` argument: a param name, or a numeric literal."""
    if token in values:
        return values[token]
    if re.fullmatch(r"-?[0-9.]+", token):
        return token
    raise SystemExit(f"sounds.md: instrument '{name}' needs value '{token}'")


def _render(template: str, values: dict[str, str], name: str) -> str:
    def expand(match: re.Match[str]) -> str:
        keys = [a.strip() for a in match.group(1).split(";")]
        if len(keys) != 3:
            raise SystemExit(f"if_steps needs 3 ';'-separated args in '{name}'")
        seq = _val(values, keys[0], name)
        grid = _val(values, keys[1], name)
        default = _val(values, keys[2], name)
        items = [v.strip() for v in seq.split("|")]
        branches = "".join(f"if(eq({grid},{i}),{v}," for i, v in enumerate(items))
        return branches + default + ")" * len(items)

    template = _IF_STEPS.sub(expand, template)
    return _simple(template, values, name)


def generate(song) -> list[str]:
    """Render every instrument in the song's ``sounds.md`` into its filter dir."""
    song.filters.mkdir(parents=True, exist_ok=True)
    text = song.sounds_md.read_text(encoding="utf-8")
    globals_ = scalars(text)
    banned = [key for key in _CLOCKS if key in globals_]
    if banned:
        raise SystemExit(
            "sounds.md: "
            + ", ".join(banned)
            + " come from song.md (bpm and bars). Delete them."
        )
    globals_ = _expand({**globals_, **_clocks(song)}, "globals")
    written: list[str] = []
    for name, template, params in rows(text, ["name", "template", "parameters"]):
        values = _expand({**globals_, **_params(params)}, name)
        body = _render(
            (C.TEMPLATES / template).read_text(encoding="utf-8"), values, name
        )
        (song.filters / f"{name}.txt").write_text(body, encoding="utf-8")
        written.append(name)
    return written
