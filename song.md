# fftechno - song arrangement

Edit this file to rearrange the track; `python -m fftechno audio` regenerates
`mix.txt` from it and re-mixes. Times are in **bars** (a bar is 4 beats).

bpm: 140
bars: 140
fade_bars: 7
sidechain_key: kick
low_bus: bass|growl

## Stems

The mix input order (one `-i` per row, top to bottom). The first column only.

| stem   |
|--------|
| kick   |
| clap   |
| hat    |
| ohat   |
| conga  |
| bass   |
| growl  |
| acid   |
| shaker |
| vox    |
| bongo  |
| rim    |
| beeps  |

## Boosts

A per-stem gain applied on top of the section gains below (used to balance the kit).

| stem   | boost |
|--------|-------|
| kick   | 2.55  |
| clap   | 2.40  |
| hat    | 2.55  |
| ohat   | 2.25  |
| conga  | 1.45  |
| shaker | 1.875 |
| bongo  | 1.95  |
| rim    | 1.95  |
| bass   | 1.15  |
| growl  | 1.00  |
| acid   | 0.78  |

## Sections

Each cell is that stem's gain during the bar range. `0.00` mutes the stem.
The **final** section fades to silence over `fade_bars`.

| bars    | kick | clap | hat  | ohat | conga | shaker | bongo | rim  | bass | growl | acid |
|---------|------|------|------|------|------|--------|-------|------|------|-------|------|
| 0-8     | 0.90 | 0.00 | 0.50 | 0.00 | 0.00 | 0.00   | 0.00  | 0.00 | 0.00 | 0.00  | 0.80 |
| 8-32    | 1.00 | 0.70 | 0.55 | 0.50 | 0.70 | 0.50   | 0.60  | 0.50 | 0.90 | 0.80  | 0.90 |
| 32-40   | 0.00 | 0.00 | 0.40 | 0.25 | 0.50 | 0.35   | 0.45  | 0.35 | 0.80 | 1.25  | 1.00 |
| 40-72   | 1.00 | 0.70 | 0.55 | 0.50 | 0.70 | 0.50   | 0.60  | 0.50 | 0.90 | 1.00  | 1.00 |
| 72-80   | 0.00 | 0.00 | 0.40 | 0.25 | 0.55 | 0.35   | 0.45  | 0.35 | 0.85 | 1.30  | 1.05 |
| 80-133  | 1.00 | 0.75 | 0.55 | 0.55 | 0.80 | 0.55   | 0.70  | 0.55 | 0.95 | 1.00  | 1.10 |
| 133-140 | 1.00 | 0.75 | 0.55 | 0.55 | 0.80 | 0.55   | 0.70  | 0.55 | 0.95 | 1.00  | 1.10 |

## Pan

Per-stem stereo placement. `mode` is `center`, `haas` (centre + Haas
widening), or `stereo` (uses `left`/`right`).

| stem   | mode   | left | right |
|--------|--------|------|-------|
| kick   | center |      |       |
| clap   | center |      |       |
| hat    | stereo | 0.62 | 0.38  |
| ohat   | stereo | 0.38 | 0.62  |
| conga  | haas   |      |       |
| shaker | stereo | 0.35 | 0.65  |
| bongo  | stereo | 0.42 | 0.58  |
| rim    | stereo | 0.62 | 0.38  |
| bass   | center |      |       |
| growl  | stereo | 0.58 | 0.42  |
| acid   | stereo | 0.42 | 0.58  |
| vox    | center |      |       |
| beeps  | center |      |       |

## Effects

Global mix effect parameters (all optional; defaults used if a row is omitted).

| effect              | value |
|---------------------|-------|
| reverb_send         | 0.7   |
| reverb_hpf          | 300   |
| reverb_wet          | 1.0   |
| sidechain_threshold | 0.03  |
| sidechain_ratio     | 12    |
| sidechain_attack    | 5     |
| sidechain_release   | 120   |
| stereo_width        | 1.3   |
| bus_threshold       | 0.1   |
| bus_ratio           | 3     |
| bus_attack          | 10    |
| bus_release         | 150   |

## Levels

Fixed level for stems that are not section-arranged (their content timing lives in
their own graphs). All stems with a Pan row must appear either in Sections, Levels
or both.

| stem  | level |
|-------|-------|
| vox   | 1.5   |
| beeps | 1.0   |
