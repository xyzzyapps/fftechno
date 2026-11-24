# fftechno - song arrangement

Oldschool acid techno: **132 BPM, 132 bars = 4:00**. A minor. Only drums and a 303.

The variation comes from three different 303 patterns - `acid_a` (dark, sparse),
`acid_b` (mid, rolling) and `acid_c` (bright, peak) - which swap across the form, so
the acid line is never the same for long. Drums enter, drop and strip back around
them.

Form: kick intro -> hats -> acid_a dark -> clap -> acid_b mid -> breakdown ->
acid_c peak -> acid_b variation -> peak -> strip -> build -> last drop -> fade.

bpm: 132
bars: 132
fade_bars: 8
sidechain_key: kick
low_bus: acid_a
reverb_seconds: 1.2

## Stems

| stem   |
|--------|
| kick   |
| clap   |
| hat    |
| ohat   |
| crash  |
| acid_a |
| acid_b |
| acid_c |

## Boosts

| stem   | boost |
|--------|-------|
| kick   | 0.80  |
| clap   | 1.40  |
| hat    | 2.20  |
| ohat   | 1.40  |
| crash  | 1.10  |
| acid_a | 1.30  |
| acid_b | 1.30  |
| acid_c | 1.30  |

## Sections

Only one acid stem plays at a time.

| bars    | kick | clap | hat  | ohat | crash | acid_a | acid_b | acid_c |
|---------|------|------|------|------|-------|--------|--------|--------|
| 0-8     | 0.85 | 0.00 | 0.00 | 0.00 | 0.00  | 0.00   | 0.00   | 0.00   |
| 8-16    | 0.90 | 0.00 | 0.45 | 0.00 | 0.00  | 0.00   | 0.00   | 0.00   |
| 16-24   | 1.00 | 0.00 | 0.60 | 0.00 | 0.00  | 0.55   | 0.00   | 0.00   |
| 24-32   | 1.00 | 0.85 | 0.70 | 0.40 | 0.40  | 0.75   | 0.00   | 0.00   |
| 32-40   | 1.00 | 0.90 | 0.75 | 0.50 | 0.40  | 0.00   | 0.85   | 0.00   |
| 40-48   | 1.00 | 0.95 | 0.85 | 0.60 | 0.50  | 0.00   | 1.00   | 0.00   |
| 48-56   | 0.00 | 0.00 | 0.25 | 0.00 | 0.00  | 0.00   | 1.00   | 0.00   |
| 56-64   | 1.00 | 0.95 | 0.90 | 0.70 | 0.70  | 0.00   | 0.00   | 0.90   |
| 64-72   | 1.00 | 1.00 | 0.95 | 0.80 | 0.60  | 0.00   | 0.00   | 1.00   |
| 72-80   | 1.00 | 0.90 | 0.85 | 0.60 | 0.50  | 0.00   | 0.95   | 0.00   |
| 80-88   | 1.00 | 1.00 | 1.05 | 0.95 | 1.00  | 0.00   | 0.00   | 1.10   |
| 88-96   | 1.00 | 1.00 | 1.05 | 0.95 | 0.90  | 0.00   | 0.00   | 1.10   |
| 96-104  | 0.90 | 0.00 | 0.30 | 0.00 | 0.00  | 0.90   | 0.00   | 0.00   |
| 104-112 | 1.00 | 0.90 | 0.80 | 0.55 | 0.50  | 0.00   | 0.95   | 0.00   |
| 112-120 | 1.00 | 1.00 | 1.05 | 0.95 | 1.00  | 0.00   | 0.00   | 1.10   |
| 120-124 | 0.70 | 0.50 | 0.50 | 0.30 | 0.20  | 0.00   | 0.60   | 0.00   |
| 124-132 | 0.25 | 0.10 | 0.15 | 0.00 | 0.00  | 0.00   | 0.20   | 0.00   |

## Pan

| stem   | mode   | left | right |
|--------|--------|------|-------|
| kick   | center |      |       |
| clap   | center |      |       |
| hat    | haas   |      |       |
| ohat   | haas   |      |       |
| crash  | haas   |      |       |
| acid_a | center |      |       |
| acid_b | center |      |       |
| acid_c | center |      |       |

## Effects

| effect              | value |
|---------------------|-------|
| reverb_send         | 0.05  |
| reverb_hpf          | 400   |
| reverb_wet          | 1.0   |
| sidechain_threshold | 0.7   |
| sidechain_ratio     | 2.5   |
| sidechain_attack    | 4     |
| sidechain_release   | 90    |
| stereo_width        | 1.00  |
| bus_threshold       | 0.15  |
| bus_ratio           | 2     |
| bus_attack          | 8     |
| bus_release         | 160   |
| master_limiter      | 0.82  |