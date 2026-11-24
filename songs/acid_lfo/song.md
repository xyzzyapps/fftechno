# fftechno - song arrangement

A 29.5-second TB-303 loop study: one acid pattern over a dry drum loop, with the
303's filter and level continuously moving like hands turning knobs.

The 303 pattern is "Acid Tabs 200" from acid-tabs.com, a square-wave 16-step
pattern in a minor scale. Pattern by J.McConaghy / Acid-Tabs.com, licensed
CC BY-SA. The notes, accents, slides and rests are reproduced exactly; the
movement is added on top by LFOs, not by changing the pattern.

Form: kick -> hats -> sub -> clap + acid -> continuous filter/envelope drift to
the end. Nothing steps; everything slides.

bpm: 130
bars: 16
fade_bars: 2
sidechain_key: kick
low_bus: sub
reverb_seconds: 1.0

## Stems

| stem |
|------|
| kick |
| clap |
| hat  |
| sub  |
| acid |

## Boosts

| stem | boost |
|------|-------|
| kick | 1.30  |
| clap | 2.60  |
| hat  | 2.80  |
| sub  | 1.10  |
| acid | 1.10  |

## Sections

| bars | kick | clap | hat  | sub  | acid |
|------|------|------|------|------|------|
| 0-3  | 0.85 | 0.00 | 0.00 | 0.00 | 0.00 |
| 3-5  | 0.95 | 0.00 | 0.55 | 0.40 | 0.00 |
| 5-7  | 1.00 | 0.00 | 0.70 | 0.80 | 0.00 |
| 7-9  | 1.00 | 0.90 | 0.80 | 0.90 | 0.55 |
| 9-14 | 1.00 | 1.00 | 0.85 | 1.00 | 1.00 |
| 14-16 | 0.30 | 0.20 | 0.25 | 0.30 | 0.25 |

Only the last row fades (`fade_bars: 2`).

## Pan

| stem | mode   | left | right |
|------|--------|------|-------|
| kick | center |      |       |
| clap | center |      |       |
| hat  | haas   |      |       |
| sub  | center |      |       |
| acid | center |      |       |

## Effects

| effect              | value |
|---------------------|-------|
| reverb_send         | 0.08  |
| reverb_hpf          | 400   |
| reverb_wet          | 1.0   |
| sidechain_threshold | 0.7   |
| sidechain_ratio     | 2.5   |
| sidechain_attack    | 4     |
| sidechain_release   | 90    |
| stereo_width        | 1.02  |
| bus_threshold       | 0.15  |
| bus_ratio           | 2     |
| bus_attack          | 8     |
| bus_release         | 160   |
| master_limiter      | 0.82  |