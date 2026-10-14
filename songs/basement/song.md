# fftechno - song arrangement

Edit this file to rearrange the track; `python -m fftechno audio` regenerates
`mix.txt` from it and re-mixes. Times are in **bars** (a bar is 4 beats).

bpm: 155
bars: 155
fade_bars: 7
sidechain_key: kick
low_bus: reese

## Stems

The mix input order (one `-i` per row, top to bottom). The first column only.

| stem      |
|-----------|
| kick      |
| snare     |
| snarefill |
| clap      |
| hat       |
| ohat      |
| ride      |
| crash     |
| breakbeat |
| shaker    |
| reese     |
| acid      |
| lead_pwm  |
| lead_fm   |
| pad       |
| stab      |
| conga     |
| vox       |

## Boosts

A per-stem gain applied on top of the section gains below (used to balance the kit).

| stem      | boost |
|-----------|-------|
| kick      | 2.20  |
| snare     | 2.00  |
| snarefill | 1.60  |
| clap      | 2.00  |
| hat       | 2.20  |
| ohat      | 2.00  |
| ride      | 1.60  |
| crash     | 1.40  |
| breakbeat | 1.80  |
| shaker    | 1.60  |
| reese     | 1.30  |
| acid      | 0.85  |
| lead_pwm  | 1.10  |
| lead_fm   | 1.10  |
| pad       | 1.20  |
| stab      | 1.30  |
| conga     | 1.50  |

## Sections

Each cell is that stem's gain during the bar range. `0.00` mutes the stem.
The **final** section fades to silence over `fade_bars`.

| bars    | kick | snare | snarefill | clap | hat  | ohat | ride | crash | breakbeat | shaker | reese | acid | lead_pwm | lead_fm | pad  | stab | conga |
|---------|------|-------|-----------|------|------|------|------|-------|-----------|--------|-------|------|----------|---------|------|------|-------|
| 0-8     | 0.00 | 0.00  | 0.00      | 0.00 | 0.35 | 0.00 | 0.00 | 1.00  | 0.60      | 0.40   | 0.00  | 0.00 | 0.00     | 0.00    | 0.40 | 0.00 | 0.00  |
| 8-24    | 1.00 | 0.70  | 0.00      | 0.60 | 0.50 | 0.40 | 0.30 | 0.90  | 0.80      | 0.50   | 0.90  | 0.50 | 0.00     | 0.00    | 0.00 | 0.30 | 0.60  |
| 24-40   | 1.00 | 0.75  | 0.00      | 0.70 | 0.55 | 0.50 | 0.40 | 0.60  | 0.85      | 0.55   | 0.95  | 0.70 | 0.80     | 0.00    | 0.00 | 0.50 | 0.70  |
| 40-48   | 0.00 | 0.00  | 0.30      | 0.00 | 0.20 | 0.00 | 0.00 | 1.00  | 0.40      | 0.30   | 0.60  | 0.30 | 0.50     | 0.80    | 1.00 | 0.00 | 0.00  |
| 48-72   | 1.00 | 0.80  | 0.00      | 0.70 | 0.55 | 0.50 | 0.45 | 0.90  | 0.90      | 0.55   | 1.00  | 0.80 | 0.90     | 0.90    | 0.00 | 0.60 | 0.80  |
| 72-80   | 0.00 | 0.30  | 0.50      | 0.00 | 0.20 | 0.00 | 0.00 | 1.00  | 0.50      | 0.30   | 0.50  | 0.40 | 0.40     | 0.70    | 0.90 | 0.00 | 0.00  |
| 80-128  | 1.00 | 0.80  | 0.00      | 0.75 | 0.60 | 0.55 | 0.50 | 0.90  | 0.95      | 0.60   | 1.00  | 0.90 | 0.90     | 0.90    | 0.00 | 0.70 | 0.85  |
| 128-148 | 1.00 | 0.85  | 0.00      | 0.75 | 0.60 | 0.55 | 0.50 | 0.90  | 0.95      | 0.60   | 1.00  | 1.00 | 1.00     | 1.00    | 0.30 | 0.80 | 0.90  |
| 148-155 | 0.90 | 0.70  | 0.60      | 0.50 | 0.40 | 0.30 | 0.30 | 0.80  | 0.70      | 0.40   | 0.80  | 0.60 | 0.50     | 0.50    | 0.60 | 0.40 | 0.50  |

## Pan

Per-stem stereo placement. `mode` is `center`, `haas` (centre + Haas
widening), or `stereo` (uses `left`/`right`).

| stem      | mode   | left | right |
|-----------|--------|------|-------|
| kick      | center |      |       |
| snare     | center |      |       |
| snarefill | center |      |       |
| clap      | center |      |       |
| hat       | stereo | 0.62 | 0.38  |
| ohat      | stereo | 0.38 | 0.62  |
| ride      | stereo | 0.55 | 0.45  |
| crash     | stereo | 0.50 | 0.50  |
| breakbeat | stereo | 0.48 | 0.52  |
| shaker    | stereo | 0.35 | 0.65  |
| reese     | center |      |       |
| acid      | stereo | 0.42 | 0.58  |
| lead_pwm  | stereo | 0.40 | 0.60  |
| lead_fm   | stereo | 0.60 | 0.40  |
| pad       | stereo | 0.50 | 0.50  |
| stab      | stereo | 0.45 | 0.55  |
| conga     | haas   |      |       |
| vox       | center |      |       |

## Effects

Global mix effect parameters (all optional; defaults used if a row is omitted).

| effect              | value |
|---------------------|-------|
| reverb_send         | 0.55  |
| reverb_hpf          | 280   |
| reverb_wet          | 1.0   |
| sidechain_threshold | 0.03  |
| sidechain_ratio     | 12    |
| sidechain_attack    | 5     |
| sidechain_release   | 120   |
| stereo_width        | 1.25  |
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
| vox   | 3.0   |
