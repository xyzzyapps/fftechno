# fftechno - song arrangement

Edit this file to rearrange the track; `python -m fftechno audio` regenerates
`mix.txt` from it and re-mixes. Times are in **bars** (a bar is 4 beats).

bpm: 140
bars: 140
fade_bars: 7

## Boosts

A per-stem gain applied on top of the section gains below (used to balance the kit).

| stem   | boost |
|--------|-------|
| kick   | 2.55  |
| clap   | 2.40  |
| hat    | 2.55  |
| ohat   | 2.25  |
| perc   | 1.95  |
| shaker | 1.875 |
| bongo  | 1.95  |
| rim    | 1.95  |
| bass   | 1.15  |
| growl  | 1.00  |
| acid   | 1.00  |

## Sections

Each cell is that stem's gain during the bar range. `0.00` mutes the stem.
The **final** section fades to silence over `fade_bars`.

| bars    | kick | clap | hat  | ohat | perc | shaker | bongo | rim  | bass | growl | acid |
|---------|------|------|------|------|------|--------|-------|------|------|-------|------|
| 0-8     | 0.90 | 0.00 | 0.50 | 0.00 | 0.00 | 0.00   | 0.00  | 0.00 | 0.00 | 0.00  | 0.80 |
| 8-32    | 1.00 | 0.70 | 0.55 | 0.50 | 0.70 | 0.50   | 0.60  | 0.50 | 0.90 | 0.80  | 0.90 |
| 32-40   | 0.00 | 0.00 | 0.40 | 0.25 | 0.50 | 0.35   | 0.45  | 0.35 | 0.80 | 1.25  | 1.00 |
| 40-72   | 1.00 | 0.70 | 0.55 | 0.50 | 0.70 | 0.50   | 0.60  | 0.50 | 0.90 | 1.00  | 1.00 |
| 72-80   | 0.00 | 0.00 | 0.40 | 0.25 | 0.55 | 0.35   | 0.45  | 0.35 | 0.85 | 1.30  | 1.05 |
| 80-133  | 1.00 | 0.75 | 0.55 | 0.55 | 0.80 | 0.55   | 0.70  | 0.55 | 0.95 | 1.00  | 1.10 |
| 133-140 | 1.00 | 0.75 | 0.55 | 0.55 | 0.80 | 0.55   | 0.70  | 0.55 | 0.95 | 1.00  | 1.10 |
