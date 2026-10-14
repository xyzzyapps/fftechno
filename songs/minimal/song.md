# fftechno - song arrangement

Edit this file to rearrange the track; `python -m fftechno audio` regenerates
`mix.txt` from it and re-mixes. Times are in **bars** (a bar is 4 beats).

Robert Hood minimal: the kick is **4-on-4 and never drops** for the whole track; the
other layers come and go to keep it interesting. 100 BPM, 75 bars = 3:00. Everything
is dry (the `Effects` reverb send is only glue), and the bass is a one-note engine
pumping against the side-chain.

The intro is a single bar of bare kick.

bpm: 100
bars: 75
fade_bars: 7
sidechain_key: kick
low_bus: bass

## Stems

The mix input order (one `-i` per row, top to bottom). The first column only.

| stem  |
|-------|
| kick  |
| hat   |
| ohat  |
| snare |
| rim   |
| bass  |
| blow  |

## Boosts

A per-stem gain applied on top of the section gains below (used to balance the kit).

| stem  | boost |
|-------|-------|
| kick  | 2.40  |
| hat   | 2.60  |
| ohat  | 2.20  |
| snare | 1.60  |
| rim   | 2.00  |
| bass  | 1.50  |
| blow  | 2.4   |

## Sections

Each cell is that stem's gain during the bar range. `0.00` mutes the stem.
The **final** section fades to silence over `fade_bars`, so it must be `fade_bars`
long for the fade to end exactly with the track (68-75, i.e. the last 7 bars, here).
The kick stays at `1.00` throughout - interest comes from the layers entering and
leaving (snare at bar 17, rim at 33, snare out again at 49 with the rim carrying it).
Only bar 0 is bare: the 4 kicks.

The `blow` stem is held at `1.00` everywhere: it is self-timed (a puff every `period`
seconds from `at` in `sounds.md`, repeated to the end of the track), and being
*arranged* rather than fixed-level is what makes its last puffs fade out with the rest.

| bars | kick | hat  | ohat | snare | rim  | bass | blow |
|------|------|------|------|-------|------|------|------|
| 0-1  | 1.00 | 0.00 | 0.00 | 0.00  | 0.00 | 0.00 | 1.00 |
| 1-17 | 1.00 | 0.35 | 0.30 | 0.00  | 0.00 | 0.65 | 1.00 |
| 17-33| 1.00 | 0.45 | 0.40 | 0.75  | 0.00 | 0.85 | 1.00 |
| 33-49| 1.00 | 0.55 | 0.50 | 0.80  | 0.60 | 1.00 | 1.00 |
| 49-68| 1.00 | 0.50 | 0.45 | 0.00  | 0.70 | 1.00 | 1.00 |
| 68-75| 0.90 | 0.40 | 0.35 | 0.70  | 0.50 | 0.80 | 1.00 |

## Pan

Per-stem stereo placement. `mode` is `center`, `haas` (centre + Haas
widening), `keep` (the stem is already stereo - e.g. the ping-pong blow - so it is
passed through untouched), or `stereo` (uses `left`/`right`). The two hats sit on opposite sides;
everything else stays centred for a focused, hypnotic image.

| stem  | mode   | left | right |
|-------|--------|------|-------|
| kick  | center |      |       |
| hat   | stereo | 0.55 | 0.45  |
| ohat  | stereo | 0.40 | 0.60  |
| snare | center |      |       |
| rim   | stereo | 0.60 | 0.40  |
| bass  | center |      |       |
| blow  | keep   |      |       |

## Effects

Global mix effect parameters (all optional; defaults used if a row is omitted).
`reverb_send` is minimal and high-passed - this is a dry, tight track.

| effect              | value |
|---------------------|-------|
| reverb_send         | 0.10  |
| reverb_hpf          | 400   |
| reverb_wet          | 1.0   |
| sidechain_threshold | 0.03  |
| sidechain_ratio     | 10    |
| sidechain_attack    | 8     |
| sidechain_release   | 160   |
| stereo_width        | 1.0   |
| bus_threshold       | 0.1   |
| bus_ratio           | 3     |
| bus_attack          | 10    |
| bus_release         | 150   |

## Levels

No stem uses a fixed level: the five `blow` puffs are section-arranged (so their last
ones fade with the track) and everything else is too. The track is instrumental: no
`vox` stem (see `vocals.md`, kept for when the ticks come back).
