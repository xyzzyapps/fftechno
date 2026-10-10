"""Markdown-driven instrument synthesis.

Define instruments in ``sounds.md`` (``name`` | ``type`` | ``parameters``) and run
``python -m fftechno synth``; each row becomes ``filters/<name>.txt`` - an ffmpeg
filtergraph ending in ``[out]`` that the audio build can render like any other
stem.

Add a new kind of sound by writing a generator function and registering it in
``GENERATORS``. Parameters are ``key=value`` pairs in the third table column.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

from . import config as C

# Generated oscillators run at 192 kHz and are anti-alias filtered on downsampling.
_SR = 192000
_TAIL = "lowpass=f=19000,aresample=48000[out]"


def _params(cell: str) -> dict[str, float]:
    """Parse a ``key=value, key=value`` parameter cell."""
    out: dict[str, float] = {}
    for part in cell.split(","):
        if "=" in part:
            key, value = part.split("=", 1)
            out[key.strip()] = float(value)
    return out


def _source(expr: str, effects: str = "") -> str:
    """Wrap a sample expression plus effect chain into a filtergraph."""
    return (f"aevalsrc='{expr}':s={_SR}:d={C.DURATION:g}[src];"
            f"[src]{effects}{_TAIL}\n")


def kick(p: dict[str, float]) -> str:
    """A 909-style 4-on-the-floor kick.

    Parameters: ``amp, f0, sweep, rate, decay, click_freq, click_decay,
    click_amt`` and optional ``bpm`` (defaults to the song BPM).
    """
    amp = p.get("amp", 0.9)
    f0 = p.get("f0", 50.0)
    sweep = p.get("sweep", 180.0)
    rate = p.get("rate", 50.0)
    decay = p.get("decay", 8.0)
    cf = p.get("click_freq", 1500.0)
    cd = p.get("click_decay", 250.0)
    ca = p.get("click_amt", 0.25)
    beat = 60.0 / p.get("bpm", C.BPM)
    tau = f"mod(t,{beat:.6f})"
    expr = (
        f"{amp:g}*(sin(2*PI*({f0:g}*{tau}+({sweep:g}/{rate:g})*(1-exp(-{rate:g}*{tau}))))"
        f"*exp(-{decay:g}*{tau})"
        f"+{ca:g}*sin(2*PI*{cf:g}*{tau})*exp(-{cd:g}*{tau}))"
    )
    return _source(expr)


def noise(p: dict[str, float]) -> str:
    """A filtered noise burst (hat / shaker / clap body).

    Parameters: ``amp, decay, hp, lp, period`` (seconds between hits).
    """
    amp = p.get("amp", 0.35)
    decay = p.get("decay", 80.0)
    hp = p.get("hp", 7000.0)
    lp = p.get("lp", 20000.0)
    period = p.get("period", 0.107143)
    tau = f"mod(t,{period:.6f})"
    return _source(f"{amp:g}*(random(0)*2-1)*exp(-{decay:g}*{tau})",
                   f"highpass=f={hp:g},lowpass=f={lp:g},")


GENERATORS: dict[str, Callable[[dict[str, float]], str]] = {
    "kick": kick,
    "noise": noise,
}


def _rows(text: str) -> list[list[str]]:
    """Return the rows of the first ``name | type | parameters`` table."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if i + 1 >= len(lines) or not line.lstrip().startswith("|"):
            continue
        if not re.match(r"^\s*\|[\s:|.-]+\|\s*$", lines[i + 1]):
            continue
        header = [c.strip().lower() for c in line.strip().strip("|").split("|")]
        if header[:3] != ["name", "type", "parameters"]:
            continue
        rows = []
        j = i + 2
        while j < len(lines) and lines[j].lstrip().startswith("|"):
            rows.append([c.strip() for c in lines[j].strip().strip("|").split("|")])
            j += 1
        return rows
    return []


def generate(sounds_path: Path | None = None) -> list[str]:
    """Write ``filters/<name>.txt`` for every instrument in ``sounds.md``."""
    path = sounds_path or (C.ROOT / "sounds.md")
    written: list[str] = []
    for name, kind, params in _rows(path.read_text(encoding="utf-8")):
        gen = GENERATORS.get(kind)
        if gen is None:
            raise SystemExit(f"unknown instrument type '{kind}' (instrument '{name}')")
        (C.FILTERS / f"{name}.txt").write_text(gen(_params(params)), encoding="utf-8")
        written.append(name)
    return written
