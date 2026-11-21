# fftechno - song arrangement

Stoner rock. **76 BPM, 76 bars = 4:00**, D minor / drop-D, instrumental, 4/4, no
samples. A hypnotic two-note fuzz riff, a thick fuzz bass, big sparse drums, a
wah-ish lead and a 5 s room. `reverb_seconds: 5.0`.

Structure: intro riff (organ under it) -> verse -> chorus -> tom breakdown -> verse ->
chorus -> lead break -> final chorus fading out.

bpm: 76
bars: 76
fade_bars: 8
sidechain_key: kick
low_bus: bass
reverb_seconds: 5.0

## Stems

| stem     |
|----------|
| kick     |
| snare    |
| tom      |
| hat      |
| ride     |
| crash    |
| bass     |
| gtr_l    |
| gtr_r    |
| gtr_lead |
| organ    |

## Boosts

| stem     | boost |
|----------|-------|
| kick     | 1.20  |
| snare    | 1.10  |
| tom      | 1.20  |
| hat      | 0.90  |
| ride     | 0.80  |
| crash    | 0.90  |
| bass     | 1.20  |
| gtr_l    | 1.00  |
| gtr_r    | 1.00  |
| gtr_lead | 2.00  |
| organ    | 0.80  |

## Sections

| bars   | kick | snare | tom  | hat  | ride | crash | bass | gtr_l | gtr_r | gtr_lead | organ |
|--------|------|-------|------|------|------|-------|------|-------|-------|----------|-------|
| 0-8    | 0.00 | 0.00  | 0.00 | 0.00 | 0.00 | 0.00  | 0.00 | 0.60  | 0.60  | 0.00     | 0.80  |
| 8-20   | 1.00 | 1.00  | 0.00 | 0.80 | 0.50 | 0.40  | 1.00 | 0.90  | 0.90  | 0.00     | 0.15  |
| 20-32  | 1.00 | 1.00  | 0.00 | 0.80 | 0.70 | 0.70  | 1.00 | 1.00  | 1.00  | 0.90     | 0.10  |
| 32-40  | 0.60 | 0.00  | 1.00 | 0.50 | 0.00 | 0.40  | 0.60 | 0.70  | 0.70  | 0.70     | 0.80  |
| 40-52  | 1.00 | 1.00  | 0.00 | 0.80 | 0.50 | 0.40  | 1.00 | 0.90  | 0.90  | 0.00     | 0.15  |
| 52-64  | 1.00 | 1.00  | 0.00 | 0.80 | 0.70 | 0.70  | 1.00 | 1.00  | 1.00  | 0.90     | 0.10  |
| 64-68  | 1.00 | 0.90  | 0.80 | 0.80 | 0.80 | 0.70  | 1.00 | 1.00  | 1.00  | 1.20     | 0.10  |
| 68-76  | 1.00 | 1.00  | 0.00 | 0.80 | 0.70 | 0.70  | 1.00 | 1.00  | 1.00  | 0.90     | 0.10  |

## Pan

| stem     | mode   | left | right |
|----------|--------|------|-------|
| kick     | center |      |       |
| snare    | center |      |       |
| tom      | center |      |       |
| hat      | stereo | 0.55 | 0.45  |
| ride     | stereo | 0.40 | 0.60  |
| crash    | stereo | 0.60 | 0.40  |
| bass     | center |      |       |
| gtr_l    | stereo | 0.80 | 0.20  |
| gtr_r    | stereo | 0.20 | 0.80  |
| gtr_lead | haas   |      |       |
| organ    | stereo | 0.45 | 0.55  |

## Effects

| effect              | value |
|---------------------|-------|
| reverb_send         | 0.45  |
| reverb_hpf          | 300   |
| reverb_wet          | 1.0   |
| sidechain_threshold | 0.12  |
| sidechain_ratio     | 1.5   |
| sidechain_attack    | 20    |
| sidechain_release   | 180   |
| stereo_width        | 1.15  |
| bus_threshold       | 0.20  |
| bus_ratio           | 1.8   |
| bus_attack          | 25    |
| bus_release         | 240   |
