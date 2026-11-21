# fftechno - song arrangement

Psychedelic 1960s rock with a wall of sound. **110 BPM, 110 bars = 4:00**, E minor,
4/4, instrumental. No samples: every sound is `aevalsrc` (see `sounds.md`). The wall
is two detuned rhythm guitars panned wide, a Farfisa-ish organ, a mellotron pad and
tambourine, all sitting in a 5.5 s convolution reverb (`reverb_seconds`).

Structure: organ/guitar swell intro -> verse -> chorus -> tom breakdown -> verse ->
chorus -> fuzz solo -> turnaround -> final chorus fading out.

bpm: 110
bars: 110
fade_bars: 8
sidechain_key: kick
low_bus: bass
reverb_seconds: 5.5

## Stems

| stem     |
|----------|
| kick     |
| snare    |
| tom      |
| hat      |
| ride     |
| crash    |
| tamb     |
| bass     |
| gtr_l    |
| gtr_r    |
| gtr_lead |
| organ    |
| pad      |

## Boosts

| stem     | boost |
|----------|-------|
| kick     | 1.20  |
| snare    | 1.40  |
| tom      | 1.30  |
| hat      | 1.10  |
| ride     | 0.90  |
| crash    | 1.10  |
| tamb     | 1.40  |
| bass     | 1.20  |
| gtr_l    | 2.20  |
| gtr_r    | 2.20  |
| gtr_lead | 1.40  |
| organ    | 1.00  |
| pad      | 0.50  |

## Sections

| bars    | kick | snare | tom  | hat  | ride | crash | tamb | bass | gtr_l | gtr_r | gtr_lead | organ | pad  |
|---------|------|-------|------|------|------|-------|------|------|-------|-------|----------|-------|------|
| 0-8     | 0.00 | 0.00  | 0.00 | 0.00 | 0.00 | 0.00  | 0.00 | 0.00 | 0.60  | 0.60  | 0.00     | 0.80  | 0.90 |
| 8-24    | 1.00 | 1.00  | 0.00 | 1.00 | 0.70 | 0.50  | 0.80 | 1.00 | 0.90  | 0.90  | 0.00     | 0.70  | 0.50 |
| 24-40   | 1.00 | 1.00  | 0.00 | 1.00 | 0.80 | 0.80  | 1.00 | 1.00 | 1.00  | 1.00  | 1.00     | 0.80  | 0.70 |
| 40-48   | 0.00 | 0.00  | 1.00 | 0.60 | 0.00 | 0.40  | 0.60 | 0.60 | 0.50  | 0.50  | 0.80     | 0.90  | 0.90 |
| 48-64   | 1.00 | 1.00  | 0.00 | 1.00 | 0.70 | 0.50  | 0.80 | 1.00 | 0.90  | 0.90  | 0.00     | 0.70  | 0.50 |
| 64-80   | 1.00 | 1.00  | 0.00 | 1.00 | 0.80 | 0.80  | 1.00 | 1.00 | 1.00  | 1.00  | 1.00     | 0.80  | 0.70 |
| 80-96   | 1.00 | 0.80  | 0.80 | 0.90 | 0.90 | 0.80  | 1.00 | 1.00 | 1.00  | 1.00  | 1.20     | 0.80  | 0.80 |
| 96-102  | 0.80 | 0.80  | 1.00 | 0.80 | 0.60 | 0.60  | 0.80 | 0.80 | 0.70  | 0.70  | 0.90     | 0.90  | 0.90 |
| 102-110 | 1.00 | 1.00  | 0.00 | 1.00 | 0.80 | 0.80  | 1.00 | 1.00 | 1.00  | 1.00  | 1.00     | 0.80  | 0.70 |

## Pan

| stem     | mode   | left | right |
|----------|--------|------|-------|
| kick     | center |      |       |
| snare    | center |      |       |
| tom      | center |      |       |
| hat      | stereo | 0.55 | 0.45  |
| ride     | stereo | 0.40 | 0.60  |
| crash    | stereo | 0.60 | 0.40  |
| tamb     | stereo | 0.65 | 0.35  |
| bass     | center |      |       |
| gtr_l    | stereo | 0.85 | 0.15  |
| gtr_r    | stereo | 0.15 | 0.85  |
| gtr_lead | haas   |      |       |
| organ    | stereo | 0.45 | 0.55  |
| pad      | haas   |      |       |

## Effects

| effect              | value |
|---------------------|-------|
| reverb_send         | 0.55  |
| reverb_hpf          | 260   |
| reverb_wet          | 1.0   |
| sidechain_threshold | 0.12  |
| sidechain_ratio     | 1.5   |
| sidechain_attack    | 20    |
| sidechain_release   | 180   |
| stereo_width        | 1.25  |
| bus_threshold       | 0.22  |
| bus_ratio           | 1.6   |
| bus_attack          | 30    |
| bus_release         | 250   |
