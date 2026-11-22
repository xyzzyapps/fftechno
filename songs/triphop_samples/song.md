# fftechno - song arrangement

Minimal instrumental trip hop: **84 BPM, 80 bars (~3:49)**. Four elements - the
**break**, the **sub**, the **electric piano**, the **vinyl dust**. Nothing else.
The break is the only drum source and the backbone; the piano changes one chord per
bar; the sub runs its own asynchronous melody but **only while the piano plays**; the
dust holds it together. A one-bar stop (39-40) sets up the drop.

Arc: break + dust -> piano + sub together (bar 16) -> a long groove -> dub space ->
one-bar stop -> drop -> space -> final -> outro back to the break, faded.

bpm: 84
bars: 80
fade_bars: 8
sidechain_key: brk
low_bus: sub

## Stems

| stem  |
|-------|
| brk   |
| sub   |
| ep    |
| vinyl |

## Boosts

| stem  | boost |
|-------|-------|
| brk   | 1.30  |
| sub   | 0.90  |
| ep    | 1.30  |
| vinyl | 0.85  |

## Sections

| bars  | brk  | sub  | ep   | vinyl |
|-------|------|------|------|-------|
| 0-8   | 0.90 | 0.00 | 0.00 | 0.80  |
| 8-16  | 0.90 | 0.00 | 0.00 | 0.80  |
| 16-24 | 0.90 | 1.00 | 0.60 | 0.80  |
| 24-32 | 0.90 | 1.00 | 0.60 | 0.80  |
| 32-39 | 0.60 | 0.70 | 0.80 | 0.80  |
| 39-40 | 0.00 | 0.00 | 0.00 | 0.80  |
| 40-48 | 1.00 | 1.00 | 0.60 | 0.80  |
| 48-56 | 1.00 | 1.00 | 0.60 | 0.80  |
| 56-64 | 0.40 | 0.50 | 0.90 | 0.80  |
| 64-72 | 0.90 | 0.90 | 0.60 | 0.80  |
| 72-80 | 0.70 | 0.40 | 0.30 | 0.80  |

## Pan

| stem  | mode   | left | right |
|-------|--------|------|-------|
| brk   | stereo | 0.50 | 0.50  |
| sub   | center |      |       |
| ep    | stereo | 0.50 | 0.50  |
| vinyl | stereo | 0.50 | 0.50  |

## Effects

| effect              | value |
|---------------------|-------|
| reverb_send         | 0.20  |
| reverb_hpf          | 300   |
| reverb_wet          | 1.0   |
| sidechain_threshold | 1.0   |
| sidechain_ratio     | 1     |
| sidechain_attack    | 12    |
| sidechain_release   | 200   |
| stereo_width        | 1.10  |
| bus_threshold       | 0.1   |
| bus_ratio           | 3     |
| bus_attack          | 10    |
| bus_release         | 180   |