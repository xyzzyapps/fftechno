"""Markdown-driven synthesis.

``sounds.md`` defines instruments (``name | template | parameters``) and global
scalars; ``templates/*.txt`` are ffmpeg filtergraphs with placeholders, rendered to
``filters/<name>.txt`` by ``python -m fftechno synth``. There are no defaults -
every placeholder must be supplied, otherwise generation fails loudly.

Template language
-----------------
``{{ key }}``                    value substitution
``{{ if_steps(SEQ; GRID; DEF) }}``  expand a comma list into a nested
                                 ``if(eq(GRID,0),v0, ... ,DEF)`` - used to build
                                 per-step melodies/patterns from markdown.
"""

from __future__ import annotations

import re
from pathlib import Path

from . import config as C

_PLACEHOLDER = re.compile(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}")
_IF_STEPS = re.compile(r"\{\{\s*if_steps\(([^}]*)\)\s*\}\}")


def _scalars(text: str) -> dict[str, str]:
    """Global ``key: value`` lines (values are substituted verbatim)."""
    return {m.group(1): m.group(2)
            for m in re.finditer(r"^\s*([a-z_]+)\s*:\s*(\S+)\s*$", text, re.M)}


def _params(cell: str) -> dict[str, str]:
    """Parse a ``key=value, key=value`` parameter cell."""
    out: dict[str, str] = {}
    for part in cell.split(","):
        if "=" in part:
            key, value = part.split("=", 1)
            out[key.strip()] = value.strip()
    return out


def _cells(line: str) -> list[str]:
    """Split a markdown table row on unescaped '|' (``\\|`` is a literal pipe)."""
    inner = line.strip()
    if inner.startswith("|"):
        inner = inner[1:]
    if inner.endswith("|") and not inner.endswith("\\|"):
        inner = inner[:-1]
    return [c.replace("\\|", "|").strip() for c in re.split(r"(?<!\\)\|", inner)]


def _rows(text: str) -> list[list[str]]:
    """Rows of the first ``name | template | parameters`` table."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if i + 1 >= len(lines) or not line.lstrip().startswith("|"):
            continue
        if not re.match(r"^\s*\|[\s:|.-]+\|\s*$", lines[i + 1]):
            continue
        header = [c.lower() for c in _cells(line)]
        if header[:3] != ["name", "template", "parameters"]:
            continue
        rows = []
        j = i + 2
        while j < len(lines) and lines[j].lstrip().startswith("|"):
            rows.append(_cells(lines[j]))
            j += 1
        return rows
    return []


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
    globals_ = _scalars(text)
    written: list[str] = []
    for name, template, params in _rows(text):
        values = {**globals_, **_params(params)}
        body = _render((C.TEMPLATES / template).read_text(encoding="utf-8"), values, name)
        (song.filters / f"{name}.txt").write_text(body, encoding="utf-8")
        written.append(name)
    return written
