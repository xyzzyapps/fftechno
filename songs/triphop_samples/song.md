# fftechno - song arrangement

Sample-based trip-hop beat (88 BPM, 8 bars ~ 21.8 s). Every sound is a **sample**
(see `sounds.md`): the TR-909 SP kit hits plus the Amen break. No oscillator
templates. It is the sample counterpart of `triphop_beat` (which synthesises the
break with `aevalsrc`).

bpm: 88
bars: 8
fade_bars: 1
sidechain_key: kick
low_bus: brk

## Stems

| stem  |
|-------|
| kick  |
| snare |
| clap  |
| hat   |
| ohat  |
| brk   |

## Boosts

| stem  | boost |
|-------|-------|
| kick  | 1.80  |
| snare | 1.40  |
| clap  | 1.20  |
| hat   | 0.90  |
| ohat  | 0.80  |
| brk   | 1.00  |

## Sections

| bars | kick | snare | clap | hat  | ohat | brk  |
|------|------|-------|------|------|------|------|
| 0-2  | 0.00 | 0.00  | 0.00 | 0.00 | 0.00 | 1.00 |
| 2-6  | 1.00 | 1.00  | 1.00 | 1.00 | 1.00 | 1.00 |
| 6-8  | 1.00 | 0.70  | 0.00 | 0.70 | 0.00 | 0.60 |

## Pan

| stem  | mode   | left | right |
|-------|--------|------|-------|
| kick  | center |      |       |
| snare | center |      |       |
| clap  | haas   |      |       |
| hat   | stereo | 0.45 | 0.55  |
| ohat  | stereo | 0.60 | 0.40  |
| brk   | stereo | 0.55 | 0.45  |

## Effects

| effect              | value |
|---------------------|-------|
| reverb_send         | 0.20  |
| reverb_hpf          | 350   |
| reverb_wet          | 0.8   |
| sidechain_threshold | 0.05  |
| sidechain_ratio     | 6     |
| sidechain_attack    | 12    |
| sidechain_release   | 200   |
| stereo_width        | 1.05  |
| bus_threshold       | 0.1   |
| bus_ratio           | 3     |
| bus_attack          | 10    |
| bus_release         | 180   |
