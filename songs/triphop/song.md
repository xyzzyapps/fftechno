# fftechno - song arrangement

Edit this file to rearrange the track; `python -m fftechno audio` regenerates
`mix.txt` from it and re-mixes. Times are in **bars** (a bar is 4 beats).

Instrumental trip hop in the DJ Shadow / DJ Krush mould. 84 BPM, 84 bars = 4:00.
D minor, one 8-bar phrase. The break is swung and bit-reduced. The boom kick is
sparse (beat 1 and the "&" of 2) and it is the side-chain key, so the sub
breathes on those hits only. The sax lead and the stacked kit are gone: the hook
is a bell figure, the space is the point.

Sections: dust and chords -> beat -> groove -> breakdown (the hook arrives) ->
drop -> space -> final -> fade. The snare roll and the reversed swell are baked
into the phrase, so they land on the bar boundaries even when the stem is up.

bpm: 84
bars: 84
fade_bars: 8
sidechain_key: kick
low_bus: sub

## Stems

The mix input order (one `-i` per row, top to bottom). The first column only.

| stem    |
|---------|
| kick    |
| brk     |
| roll    |
| sub     |
| ep      |
| strings |
| bell    |
| stab    |
| horn    |
| rise    |
| vinyl   |

## Boosts

A per-stem gain applied on top of the section gains below (used to balance the kit).

| stem    | boost |
|---------|-------|
| kick    | 1.25  |
| brk     | 3.20  |
| roll    | 2.40  |
| sub     | 0.55  |
| ep      | 1.60  |
| strings | 1.70  |
| bell    | 2.90  |
| stab    | 4.80  |
| horn    | 1.35  |
| rise    | 1.40  |
| vinyl   | 2.00  |

## Sections

Each cell is that stem's gain during the bar range. `0.00` mutes the stem.
The **final** section fades to silence over `fade_bars`. `vinyl` stays up as the
bed, then fades with the outro.

| bars  | kick | brk  | roll | sub  | ep   | strings | bell | stab | horn | rise | vinyl |
|-------|------|------|------|------|------|---------|------|------|------|------|-------|
| 0-8   | 0.00 | 0.00 | 0.00 | 0.15 | 0.80 | 0.75    | 0.00 | 0.00 | 0.00 | 0.55 | 0.90  |
| 8-20  | 0.90 | 0.85 | 0.70 | 0.90 | 0.50 | 0.30    | 0.00 | 0.35 | 0.00 | 0.30 | 0.55  |
| 20-32 | 1.00 | 1.00 | 1.00 | 1.00 | 0.48 | 0.32    | 0.00 | 0.60 | 0.25 | 0.35 | 0.50  |
| 32-40 | 0.00 | 0.00 | 0.00 | 0.22 | 0.90 | 0.85    | 0.80 | 0.70 | 0.70 | 0.50 | 0.80  |
| 40-56 | 1.00 | 1.00 | 1.00 | 1.00 | 0.42 | 0.35    | 0.90 | 0.55 | 0.45 | 0.40 | 0.48  |
| 56-64 | 0.40 | 0.00 | 0.00 | 0.75 | 0.85 | 0.80    | 0.35 | 0.20 | 0.55 | 0.40 | 0.75  |
| 64-76 | 1.00 | 1.00 | 1.00 | 1.00 | 0.45 | 0.40    | 0.85 | 0.60 | 0.50 | 0.40 | 0.48  |
| 76-84 | 0.65 | 0.60 | 0.40 | 0.60 | 0.55 | 0.50    | 0.30 | 0.15 | 0.25 | 0.15 | 0.75  |

## Pan

Per-stem stereo placement. `mode` is `center`, `haas` (centre + Haas
widening), `keep` (the stem is already stereo - the dub stab - so it is
passed through untouched), or `stereo` (uses `left`/`right`).

| stem    | mode   | left | right |
|---------|--------|------|-------|
| kick    | center |      |       |
| brk     | center |      |       |
| roll    | center |      |       |
| sub     | center |      |       |
| ep      | stereo | 0.42 | 0.58  |
| strings | haas   |      |       |
| bell    | stereo | 0.64 | 0.36  |
| stab    | keep   |      |       |
| horn    | stereo | 0.36 | 0.64  |
| rise    | stereo | 0.40 | 0.60  |
| vinyl   | stereo | 0.50 | 0.50  |

## Effects

Global mix effect parameters. The reverb is a short dark room, not a wash.
The side-chain is slow: the boom is sparse, and the sub should breathe, not pump.

| effect              | value |
|---------------------|-------|
| reverb_send         | 0.40  |
| reverb_hpf          | 180   |
| reverb_wet          | 0.85  |
| sidechain_threshold | 0.06  |
| sidechain_ratio     | 3     |
| sidechain_attack    | 18    |
| sidechain_release   | 280   |
| stereo_width        | 1.15  |
| bus_threshold       | 0.12  |
| bus_ratio           | 2     |
| bus_attack          | 20    |
| bus_release         | 220   |

## Levels

No stem uses a fixed level: every stem is section-arranged above, so all of
them fade with the outro.
