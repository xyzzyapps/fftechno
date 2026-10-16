"""One markdown reader for ``song.md``, ``sounds.md``, ``vocals.md`` and ``video.md``.

Tables split on ``|``. A ``\\|`` inside a cell is a literal pipe (step lists).
Scalars are ``key: value`` lines whose value is a single token.
"""

from __future__ import annotations

import re

_SEP = re.compile(r"^\s*\|[\s:|.-]+\|\s*$")
_SCALAR = re.compile(r"^\s*([a-z_]+)\s*:\s*(\S+)\s*$", re.MULTILINE)


def cells(line: str) -> list[str]:
    """Split a markdown table row on unescaped ``|``."""
    inner = line.strip().removeprefix("|")
    if inner.endswith("|") and not inner.endswith("\\|"):
        inner = inner[:-1]
    return [c.replace("\\|", "|").strip() for c in re.split(r"(?<!\\)\|", inner)]


def scalars(text: str) -> dict[str, str]:
    """``key: value`` lines. The value is one token, substituted verbatim."""
    return {m.group(1): m.group(2) for m in _SCALAR.finditer(text)}


def tables(text: str) -> list[tuple[list[str], list[list[str]]]]:
    """Every markdown table as ``(header cells, body rows)``."""
    found: list[tuple[list[str], list[list[str]]]] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].lstrip().startswith("|") and i + 1 < len(lines) and _SEP.match(lines[i + 1]):
            header = cells(lines[i])
            rows: list[list[str]] = []
            j = i + 2
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                rows.append(cells(lines[j]))
                j += 1
            found.append((header, rows))
            i = j
        else:
            i += 1
    return found


def rows(text: str, header: list[str]) -> list[list[str]]:
    """Body rows of the first table whose header matches *header* (case-insensitive)."""
    want = [h.lower() for h in header]
    for head, body in tables(text):
        if [c.lower() for c in head] == want:
            return body
    return []
