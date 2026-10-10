"""Markdown-driven synthesis.

``sounds.md`` defines instruments (``name | template | parameters``) and global
scalars; ``templates/*.txt`` are ffmpeg filtergraphs with ``{{key}}`` placeholders.
``python -m fftechno synth`` renders each instrument to ``filters/<name>.txt``.

There are no defaults: every ``{{key}}`` an instrument uses must be supplied by the
globals or its own parameters, otherwise generation fails loudly.
"""

from __future__ import annotations

import re
from pathlib import Path

from . import config as C

_PLACEHOLDER = re.compile(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}")


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


def _rows(text: str) -> list[list[str]]:
    """Rows of the first ``name | template | parameters`` table."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if i + 1 >= len(lines) or not line.lstrip().startswith("|"):
            continue
        if not re.match(r"^\s*\|[\s:|.-]+\|\s*$", lines[i + 1]):
            continue
        header = [c.strip().lower() for c in line.strip().strip("|").split("|")]
        if header[:3] != ["name", "template", "parameters"]:
            continue
        rows = []
        j = i + 2
        while j < len(lines) and lines[j].lstrip().startswith("|"):
            rows.append([c.strip() for c in lines[j].strip().strip("|").split("|")])
            j += 1
        return rows
    return []


def _render(template: str, values: dict[str, str], name: str) -> str:
    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in values:
            raise SystemExit(f"sounds.md: instrument '{name}' needs value '{key}'")
        return values[key]
    return _PLACEHOLDER.sub(repl, template)


def generate(sounds_path: Path | None = None) -> list[str]:
    """Render every instrument in ``sounds.md`` into ``filters/<name>.txt``."""
    path = sounds_path or C.SOUNDS
    text = path.read_text(encoding="utf-8")
    globals_ = _scalars(text)
    written: list[str] = []
    for name, template, params in _rows(text):
        values = {**globals_, **_params(params)}
        body = _render((C.TEMPLATES / template).read_text(encoding="utf-8"), values, name)
        (C.FILTERS / f"{name}.txt").write_text(body, encoding="utf-8")
        written.append(name)
    return written
