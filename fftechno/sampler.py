"""Sample playback graphs: drum-kit hits, pitched instruments and breaks.

A synth stem (``templates/*.txt``) makes sound with ``aevalsrc``. A *sampler* stem
instead reads an audio file with the ``amovie`` source filter and places copies of it
on the 16th-note grid with ``adelay``, summing them with ``amix``. The result is the
same kind of node: it is written to ``filters/<song>/<name>.txt`` and rendered and
mixed by the normal pipeline (``synth.generate`` -> ``audio.render_stems``).

A song adds a ``## Samplers`` table to its ``sounds.md``::

    | name | sample                        | params                     |
    |------|-------------------------------|----------------------------|
    | kick | samples/triphop_kit/kick.wav  | pat=0\\|6\\|10, gain=1.1        |
    | gtr  | samples/stoner_kit/gtr_c2.wav | pat=0\\|2, notes=65.41\\|77.78, root=65.41 |

A ``sample`` cell is either one path or a ``|``-separated map of ``path@root`` zones,
e.g. ``gtr_c2.wav@65.41|gtr_f2.wav@87.31|gtr_c3.wav@130.81``. Each hit uses the zone
with the nearest root (in semitones), so a wide riff shifts each sample less.

Parameters (``key=value``, comma separated):

``pat``   16th-step indices inside the pattern, looped (the pattern is built once
          and looped with ``aloop``). Spans ``pat_bars`` bars (default 1).
``pat_bars``  number of bars the ``pat`` pattern spans (default 1).
``hits``  absolute 16th steps from the song start (for sparse sounds, e.g. a break
          every two bars). Use ``pat`` or ``hits``, not both.
``vel``   per-hit velocity, parallel to ``pat``/``hits`` (default: 1 for every hit).
``notes`` per-hit frequency in Hz, parallel to ``pat``/``hits``.
``chord`` frequency ratios per hit for a power chord, e.g. ``1|1.5:0.7|2:0.45``
          (root, fifth at 0.7 velocity, octave at 0.45). Needs ``notes``.
``rr``    round-robin sample list (``|``-separated paths); successive hits cycle
          through them (kills the machine-gun effect on drums). Overrides the map.
``jitter`` per-hit timing humanize in milliseconds (deterministic, +/- that much).
``root``  the recorded frequency for a *single* sample (ignored when the cell is a
          map). Each hit is pitched by ``note / root`` with ``asetrate``.
``trim``  seconds each copy plays (default: the whole file).
``rate``  base varispeed factor (``asetrate``; applied after the note pitch).
``tempo`` ``atempo`` factor: changes speed but keeps pitch.
``fx``    extra filters applied to each hit, ``;``-separated (``;`` becomes ``,``),
          e.g. ``highpass=f=60;lowpass=f=6000;asoftclip=type=tanh:threshold=0.8``.
``gain``  per-instrument gain (default: 1).

The graphs reference the sample by a path relative to the repo root
(``samples/...``); the stem render runs with the repo root as its working directory
so the path resolves.
"""

from __future__ import annotations

import math

from . import config as C

_EXTRA = (
    "pat",
    "pat_bars",
    "hits",
    "vel",
    "notes",
    "root",
    "chord",
    "rr",
    "jitter",
    "trim",
    "rate",
    "tempo",
    "fx",
    "gain",
)


def _num(value: float) -> str:
    """A decimal ffmpeg can parse (no trailing zeros)."""
    return f"{value:.12f}".rstrip("0").rstrip(".")


def _params(cell: str) -> dict[str, str]:
    """Parse a ``key=value, key=value`` parameter cell."""
    out: dict[str, str] = {}
    for part in cell.split(","):
        if "=" in part:
            key, value = part.split("=", 1)
            out[key.strip()] = value.strip()
    for key in out:
        if key not in _EXTRA:
            raise SystemExit(
                f"sounds.md: sampler has unknown param '{key}' "
                f"(have: {', '.join(_EXTRA)})"
            )
    return out


def _sample_map(sample: str, params: dict[str, str]) -> list[tuple[str, float | None]]:
    """``(path, root)`` zones from the sample cell (one path, or ``path@root|...``)."""
    entries: list[tuple[str, float | None]] = []
    for part in sample.split("|"):
        part = part.strip()
        if not part:
            continue
        if "@" in part:
            path, root = part.rsplit("@", 1)
            entries.append((path.strip(), float(root)))
        else:
            root = float(params["root"]) if "root" in params else None
            entries.append((part, root))
    if not entries:
        raise SystemExit("sounds.md: sampler has an empty sample")
    return entries


def _instances(song, params: dict[str, str]) -> list[tuple[int, float, float | None]]:
    """``(absolute_16th_step, velocity, note)`` for every hit a sampler plays."""
    pat, hits = params.get("pat"), params.get("hits")
    if bool(pat) == bool(hits):
        raise SystemExit("sounds.md: sampler needs exactly one of 'pat' or 'hits'")
    raw = [int(x) for x in (pat or hits).split("|") if x.strip()]
    velocities = (
        [float(x) for x in params["vel"].split("|")] if "vel" in params else None
    )
    if velocities is not None and len(velocities) != len(raw):
        raise SystemExit("sounds.md: sampler 'vel' must match 'pat'/'hits' length")
    notes = (
        [float(x) for x in params["notes"].split("|")] if "notes" in params else None
    )
    if notes is not None and len(notes) != len(raw):
        raise SystemExit("sounds.md: sampler 'notes' must match 'pat'/'hits' length")
    out: list[tuple[int, float, float | None]] = []
    for index, step in enumerate(raw):
        # `pat` is a step index inside the pattern (0..pat_bars*16-1) and the pattern
        # is looped; `hits` is absolute from the song start and is placed once.
        out.append(
            (
                step,
                velocities[index] if velocities else 1.0,
                notes[index] if notes else None,
            )
        )
    if "chord" in params and notes is not None:
        # Power chord: each hit also sounds at the given frequency ratios
        # (`chord=1|1.5:0.7|2:0.45` = root, fifth at 0.7, octave at 0.45).
        intervals: list[tuple[float, float]] = []
        for part in params["chord"].split("|"):
            if ":" in part:
                ratio, mult = part.split(":", 1)
                intervals.append((float(ratio), float(mult)))
            else:
                intervals.append((float(part), 1.0))
        expanded: list[tuple[int, float, float | None]] = []
        for step, vel, note in out:
            for ratio, mult in intervals:
                expanded.append((step, vel * mult, note * ratio))
        return expanded
    return out


def _chain(
    params: dict[str, str], note: float | None, root: float | None, tail: str
) -> str:
    """The per-hit filter chain (resample, pitch, trim, FX, gain, delay)."""
    parts = ["aresample=48000", "aformat=sample_fmts=fltp:channel_layouts=mono"]
    if note is not None:
        if root is None:
            raise SystemExit("sounds.md: sampler 'notes' needs a root")
        ratio = note / root
        parts += [f"asetrate={round(48000 * ratio)}", "aresample=48000"]
    if "rate" in params:
        parts += [f"asetrate={round(48000 * float(params['rate']))}", "aresample=48000"]
    if "tempo" in params:
        parts.append(f"atempo={params['tempo']}")
    if "trim" in params:
        parts.append(f"atrim=0:{params['trim']}")
    parts.append("asetpts=N/SR/TB")
    if "fx" in params:
        parts.append(params["fx"].replace(";", ","))
    parts.append(tail)
    return ",".join(parts)


def _jitter(i: int, jitter_ms: float) -> float:
    """Deterministic humanize offset in ms, in ``[-jitter_ms, +jitter_ms]``."""
    if jitter_ms <= 0:
        return 0.0
    h = (i * 2654435761) & 0xFFFFFFFF
    frac = (h % 10000) / 10000.0
    return (frac - 0.5) * 2 * jitter_ms


def _nearest(note: float, zones: list[tuple[str, float | None]]) -> int:
    """Index of the zone whose root is closest to *note* (semitones)."""
    distances = [
        abs(math.log2(note / root)) if root else float("inf") for _path, root in zones
    ]
    return min(range(len(zones)), key=distances.__getitem__)


def graph(song, sample: str, params_cell: str) -> str:
    """The ``-/filter_complex`` body for one sampler instrument."""
    params = _params(params_cell)
    if "rr" in params:
        # Round-robin: successive hits cycle through the listed samples.
        zones = [(p.strip(), None) for p in params["rr"].split("|") if p.strip()]
    else:
        zones = _sample_map(sample, params)
    for path, _root in zones:
        if not (C.ROOT / path).exists():
            raise SystemExit(
                f"sounds.md: sampler sample '{path}' not found "
                "(run `python -m fftechno samples`)"
            )
    step_ms = song.bar / 16.0 * 1000.0
    gain = float(params.get("gain", 1))
    jitter_ms = float(params.get("jitter", 0))
    instances = _instances(song, params)
    count = len(instances)

    groups: dict[int, list[int]] = {}
    for i, (_step, _velocity, note) in enumerate(instances):
        if "rr" in params:
            zone = i % len(zones)
        elif note is not None and len(zones) > 1:
            zone = _nearest(note, zones)
        else:
            zone = 0
        groups.setdefault(zone, []).append(i)

    labels: list[str] = []
    lines: list[str] = []
    for zone in sorted(groups):
        path, root = zones[zone]
        hits = groups[zone]
        lines.append(f"amovie={path}[s{zone}]")
        if len(hits) > 1:
            lines.append(
                f"[s{zone}]asplit={len(hits)}"
                + "".join(f"[s{zone}_{k}]" for k in range(len(hits)))
            )
        for k, i in enumerate(hits):
            src = f"s{zone}" if len(hits) == 1 else f"s{zone}_{k}"
            step, velocity, note = instances[i]
            volume = _num(gain * velocity)
            delay = _num(max(0.0, step * step_ms + _jitter(i, jitter_ms)))
            chain = _chain(params, note, root, f"volume={volume},adelay={delay}:all=1")
            lines.append(f"[{src}]{chain}[h{i}]")
            labels.append(f"[h{i}]")

    duration = _num(song.duration)
    if "pat" in params:
        # `pat` is one pattern (pat_bars bars, default 1): build it once and loop
        # it (sample-accurate with asetpts + whole_len). This keeps a 4-minute
        # pattern to a handful of filters instead of one chain per hit.
        pat_bars = int(params.get("pat_bars", 1))
        loop_sec = song.bar * pat_bars
        bar = _num(loop_sec)
        frames = round(loop_sec * 48000)
        lines.append(
            "".join(labels)
            + f"amix=inputs={count}:normalize=0,asoftclip=type=tanh:threshold=0.9,"
            + f"asetpts=N/SR/TB,atrim=0:{bar},apad=whole_len={frames},"
            + f"aloop=loop=-1:size={frames},atrim=0:{duration}[out]"
        )
    else:
        # Sparse absolute hits: place each one and pad with a silent bed so the
        # stem is exactly `song.duration`.
        lines.append(
            f"aevalsrc='0':s=48000:d={duration},"
            "aformat=sample_fmts=fltp:channel_layouts=mono[bed]"
        )
        lines.append(
            "".join(labels)
            + f"[bed]amix=inputs={count + 1}:normalize=0:duration=longest,"
            + "asoftclip=type=tanh:threshold=0.9[out]"
        )
    return ";\n".join(lines) + "\n"
