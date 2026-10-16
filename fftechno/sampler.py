"""Sample playback graphs: drum-kit hits and breaks.

A synth stem (``templates/*.txt``) makes sound with ``aevalsrc``. A *sampler* stem
instead reads an audio file with the ``amovie`` source filter and places copies of it
on the 16th-note grid with ``adelay``, summing them with ``amix``. The result is the
same kind of node: it is written to ``filters/<song>/<name>.txt`` and rendered and
mixed by the normal pipeline (``synth.generate`` -> ``audio.render_stems``).

A song adds a ``## Samplers`` table to its ``sounds.md``::

    | name | sample                        | params                     |
    |------|-------------------------------|----------------------------|
    | kick | samples/triphop_kit/kick.wav  | pat=0\\|6\\|10, gain=1.1        |
    | brk  | samples/breaks/amen.wav       | hits=0\\|32\\|64, rate=0.81     |

Parameters (``key=value``, comma separated):

``pat``   16th steps (0-15) inside one bar, repeated on every bar.
``hits``  absolute 16th steps from the song start (for sparse sounds, e.g. a break
          every two bars). Use ``pat`` or ``hits``, not both.
``vel``   per-hit velocity, parallel to ``pat``/``hits`` (default: 1 for every hit).
``trim``  seconds each copy plays (default: the whole file).
``rate``  varispeed factor (``asetrate``; below 1 is slower and lower - the trip-hop
          trick). Pitch and speed move together.
``tempo`` ``atempo`` factor: changes speed but keeps pitch.
``gain``  per-instrument gain (default: 1).

The graphs reference the sample by a path relative to the repo root
(``samples/...``); the stem render runs with the repo root as its working directory
so the path resolves.
"""

from __future__ import annotations

from . import config as C

_EXTRA = ("pat", "hits", "vel", "trim", "rate", "tempo", "gain")


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


def _instances(song, params: dict[str, str]) -> list[tuple[int, float]]:
    """``(absolute_16th_step, velocity)`` for every hit a sampler plays."""
    pat, hits = params.get("pat"), params.get("hits")
    if bool(pat) == bool(hits):
        raise SystemExit("sounds.md: sampler needs exactly one of 'pat' or 'hits'")
    raw = [int(x) for x in (pat or hits).split("|") if x.strip()]
    velocities = (
        [float(x) for x in params["vel"].split("|")] if "vel" in params else None
    )
    if velocities is not None and len(velocities) != len(raw):
        raise SystemExit("sounds.md: sampler 'vel' must match 'pat'/'hits' length")
    steps = range(song.arrangement().bars) if pat else (0,)
    out: list[tuple[int, float]] = []
    for bar in steps:
        for index, step in enumerate(raw):
            absolute = bar * 16 + step if pat else step
            out.append((absolute, velocities[index] if velocities else 1.0))
    return out


def _chain(params: dict[str, str], tail: str) -> str:
    """The per-hit filter chain (resample, optional varispeed/tempo, trim, ...)."""
    parts = ["aresample=48000", "aformat=sample_fmts=fltp:channel_layouts=mono"]
    if "rate" in params:
        parts += [f"asetrate={round(48000 * float(params['rate']))}", "aresample=48000"]
    if "tempo" in params:
        parts.append(f"atempo={params['tempo']}")
    if "trim" in params:
        parts.append(f"atrim=0:{params['trim']}")
    parts += ["asetpts=N/SR/TB", tail]
    return ",".join(parts)


def graph(song, sample: str, params_cell: str) -> str:
    """The ``-/filter_complex`` body for one sampler instrument."""
    params = _params(params_cell)
    if not (C.ROOT / sample).exists():
        raise SystemExit(
            f"sounds.md: sampler sample '{sample}' not found "
            "(run `python -m fftechno samples`)"
        )
    step_ms = song.bar / 16.0 * 1000.0
    gain = float(params.get("gain", 1))
    instances = _instances(song, params)
    count = len(instances)

    labels: list[str] = []
    lines = [f"amovie={sample}[s]"]
    if count > 1:
        lines.append(f"[s]asplit={count}" + "".join(f"[s{i}]" for i in range(count)))
    for i, (step, velocity) in enumerate(instances):
        src = "s" if count == 1 else f"s{i}"
        volume = _num(gain * velocity)
        delay = _num(step * step_ms)
        chain = _chain(params, f"volume={volume},adelay={delay}:all=1")
        lines.append(f"[{src}]{chain}[h{i}]")
        labels.append(f"[h{i}]")

    duration = _num(song.duration)
    # A silent bed of the whole song length keeps the stem exactly `song.duration`
    # regardless of where the last hit falls. Plain `apad` here would make ffmpeg's
    # `-t` cut the stem short, and `anullsrc` does not carry its length into `amix`.
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
