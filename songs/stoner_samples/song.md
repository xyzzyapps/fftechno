# fftechno - song arrangement

Sample-based stoner rock. **80 BPM, 80 bars = 4:00**, C minor / drop-C, instrumental.
Every sound is a downloaded sample (FreePats distorted guitar + picked bass, Pearl
Master Studio drums), sequenced with the sampler. `reverb_seconds: 5.0`.

The riff is the drop-C minor figure C-C-Eb-F / C-C-Eb-G in 8th notes, doubled by two
detuned guitars panned wide. Structure: intro riff -> verse -> chorus -> tom
breakdown -> verse -> chorus -> lead break -> final chorus fading out.

bpm: 80
bars: 80
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
| gtr_l    | 1.20  |
| gtr_r    | 1.20  |
| gtr_lead | 1.60  |

## Sections

| bars   | kick | snare | tom  | hat  | ride | crash | bass | gtr_l | gtr_r | gtr_lead |
|--------|------|-------|------|------|------|-------|------|-------|-------|----------|
| 0-8    | 0.00 | 0.00  | 0.00 | 0.00 | 0.00 | 0.00  | 0.00 | 0.60  | 0.60  | 0.00     |
| 8-20   | 1.00 | 1.00  | 0.00 | 0.80 | 0.50 | 0.40  | 1.00 | 0.90  | 0.90  | 0.00     |
| 20-32  | 1.00 | 1.00  | 0.00 | 0.80 | 0.70 | 0.70  | 1.00 | 1.00  | 1.00  | 0.90     |
| 32-40  | 0.60 | 0.00  | 1.00 | 0.50 | 0.00 | 0.40  | 0.60 | 0.70  | 0.70  | 0.70     |
| 40-52  | 1.00 | 1.00  | 0.00 | 0.80 | 0.50 | 0.40  | 1.00 | 0.90  | 0.90  | 0.00     |
| 52-64  | 1.00 | 1.00  | 0.00 | 0.80 | 0.70 | 0.70  | 1.00 | 1.00  | 1.00  | 0.90     |
| 64-72  | 1.00 | 0.90  | 0.80 | 0.80 | 0.80 | 0.70  | 1.00 | 1.00  | 1.00  | 1.20     |
| 72-80  | 1.00 | 1.00  | 0.00 | 0.80 | 0.70 | 0.70  | 1.00 | 1.00  | 1.00  | 0.90     |

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

## Effects

| effect              | value |
|---------------------|-------|
| reverb_send         | 0.40  |
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
