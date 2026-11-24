# fftechno - synth definitions

TB-303 pattern study with tribal drums, **130 BPM**. Drums plus three squelch
voicings of one acid pattern.

## Attribution

The 303 pattern is **"Acid Tabs 200"** from
[acid-tabs.com](https://acid-tabs.com/303_patterns.php?Pattern_Select=QWNpZCBUYWJzIDIwMCAtIFRCLTMwMyBQYXR0ZXJu):

- Pattern by **J.McConaghy / Acid-Tabs.com**
- Licensed **CC BY-SA** (commercial use allowed with attribution; adaptations must
  be shared under the same terms)
- 130 BPM, square wave, no triplets, minor scale

The notes below are a transcription of that published pattern. If this track is
published, the licence terms must be settled with the author.

## The pattern (exact)

| Step | Note | Octave | Hz | Accent | Slide | Gate |
|---|---|---|---|---|---|---|
| 1 | B | 0 | 246.94 | 1.0 | 0 | 1 |
| 2 | C | -1 | 123.47 | 0.5 | 1 | 1 |
| 3 | B | 0 | 246.94 | 0.5 | 0 | 1 |
| 4 | C | -1 | 123.47 | 1.0 | 0 | 1 |
| 5 | D | 0 | 293.66 | 1.0 | 0 | 1 |
| 6 | F# | -1 | 185.00 | 1.0 | 0 | 1 |
| 7 | B | 0 | 246.94 | 1.0 | 0 | 1 |
| 8 | tie | | 246.94 | 0.5 | 0 | 1 |
| 9 | B | 0 | 246.94 | 0.5 | 0 | 1 |
| 10 | G | +1 | 783.99 | 1.0 | 0 | 1 |
| 11 | rest | | 246.94 | 1.0 | 0 | 0 |
| 12 | B | 0 | 246.94 | 1.0 | 0 | 1 |
| 13 | A | -1 | 220.00 | 0.5 | 1 | 1 |
| 14 | D | +1 | 587.33 | 0.5 | 0 | 1 |
| 15 | C+ | 0 | 277.18 | 0.5 | 0 | 1 |
| 16 | D | -1 | 146.83 | 0.5 | 0 | 1 |

The step-8 tie holds the step-7 note; step 11 is a rest. A square wave is used, as
specified.

## The three acid voicings

All three play the **same notes, accents, slides and gates**. Only the squelch
voicing changes, so the pattern stays exact and the variation comes from tone:

- `acid_a` - dark tribal: low mid band, narrow squelch, minimal crush.
- `acid_b` - rolling: mid band higher, more accent movement.
- `acid_c` - peak: bright band open, wide squelch, a touch more drive.

## Instruments

`bar`, `step`, `beat` and `dur` come from `song.md`. `grid` is the 16-step bar
clock. The 303 envelope is gated per step; the accent value drives a three-band
resonant squelch that decays after each accent.

sr: 192000
lp: 16000
osr: 48000
grid: floor(mod(t,{{bar}})/{{step}})
bassgrid: floor(mod(t,{{bar}}*2)/{{step}})

| name   | template        | parameters |
|--------|-----------------|------------|
| kick   | kick.txt        | amp=0.95, f0=48, sweep=230, rate=58, decay=26, click_amt=0.5, click_f=1400, click_decay=380, sub_amt=0.55, sub_f=45, sub_decay=16, noise_amt=0.28, noise_decay=280, eq_f=58, eq_g=3.5, clip=0.85 |
| clap   | clap.txt        | amp=1.0, decay1=26, tone_amt=0.65, tone_f=200, decay2=42, hp=700, lpc=11000 |
| hat    | hat_step.txt    | amp=0.4, decay=90, hp=7500, gates=1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1, vel=1.0\|0.5\|0.75\|0.5\|1.0\|0.5\|0.75\|0.5\|1.0\|0.5\|0.75\|0.5\|1.0\|0.5\|0.75\|0.5 |
| ohat   | ohat.txt        | amp=0.5, decay=15, hp=6500, off=0.230769, win=0.20 |
| sub    | sub_bounce.txt  | amp=0.55, atk=90, dec=9, harm=0.18, note_def=55, gates=1\|0\|0\|1\|0\|0\|1\|0\|1\|0\|0\|1\|0\|0\|1\|0, notes=55\|55\|55\|55\|55\|55\|55\|55\|61.74\|61.74\|61.74\|61.74\|61.74\|61.74\|61.74\|61.74, hp=30, lp_bass=120, lp_q=0.7, eq_f=50, eq_g=5, sub_cut=60, sub_boost=8, sub_dry=0.5, sub_wet=1, clip=0.85, lp=6000, grid={{bassgrid}} |
| shaker | shaker.txt      | amp=0.35, decay=60, hp=5000, vbase=0.6, vamt=0.4, gold=1.7, gates=0\|0\|1\|0\|0\|0\|1\|0\|0\|0\|1\|0\|0\|1\|1\|0 |
| acid_a | acid_squelch.txt | amp=1.0, atk=40, decay=6, acc_def=0.6, accents=1.0\|0.5\|0.5\|1.0\|1.0\|1.0\|1.0\|0.5\|0.5\|1.0\|1.0\|1.0\|0.5\|0.5\|0.5\|0.5, gates=1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|0\|1\|1\|1\|1\|1, note_def=246.94, notes=246.94\|123.47\|246.94\|123.47\|293.66\|185\|246.94\|246.94\|246.94\|783.99\|246.94\|246.94\|220\|587.33\|277.18\|146.83, slides=0\|1\|0\|0\|0\|0\|0\|0\|0\|0\|0\|0\|1\|0\|0\|0, slide_rate=22, vib_amt=0.012, vib_f=5.5, hp=50, square=0.6, dark_lp=320, dark_q=3, mid_lp=720, mid_q=2.5, bright_lp=1300, bright_q=2, dg_base=0.85, dg_amt=0.40, mg_base=0.18, mg_amt=0.42, bg_base=0.04, bg_amt=0.14, filter_decay=10, filter_f=650, filter_q=2, clip=0.55, cb=6, cm=0.06, lp=5000 |
| acid_b | acid_squelch.txt | amp=1.0, atk=35, decay=5, acc_def=0.6, accents=1.0\|0.5\|0.5\|1.0\|1.0\|1.0\|1.0\|0.5\|0.5\|1.0\|1.0\|1.0\|0.5\|0.5\|0.5\|0.5, gates=1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|0\|1\|1\|1\|1\|1, note_def=246.94, notes=246.94\|123.47\|246.94\|123.47\|293.66\|185\|246.94\|246.94\|246.94\|783.99\|246.94\|246.94\|220\|587.33\|277.18\|146.83, slides=0\|1\|0\|0\|0\|0\|0\|0\|0\|0\|0\|0\|1\|0\|0\|0, slide_rate=26, vib_amt=0.015, vib_f=5.8, hp=50, square=0.6, dark_lp=430, dark_q=3.5, mid_lp=1000, mid_q=3, bright_lp=1750, bright_q=2.5, dg_base=0.80, dg_amt=0.45, mg_base=0.22, mg_amt=0.50, bg_base=0.05, bg_amt=0.18, filter_decay=9, filter_f=900, filter_q=2.5, clip=0.6, cb=6, cm=0.08, lp=6000 |
| acid_c | acid_squelch.txt | amp=1.05, atk=30, decay=5, acc_def=0.6, accents=1.0\|0.5\|0.5\|1.0\|1.0\|1.0\|1.0\|0.5\|0.5\|1.0\|1.0\|1.0\|0.5\|0.5\|0.5\|0.5, gates=1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|0\|1\|1\|1\|1\|1, note_def=246.94, notes=246.94\|123.47\|246.94\|123.47\|293.66\|185\|246.94\|246.94\|246.94\|783.99\|246.94\|246.94\|220\|587.33\|277.18\|146.83, slides=0\|1\|0\|0\|0\|0\|0\|0\|0\|0\|0\|0\|1\|0\|0\|0, slide_rate=30, vib_amt=0.018, vib_f=6.2, hp=50, square=0.6, dark_lp=520, dark_q=4, mid_lp=1250, mid_q=3.5, bright_lp=2200, bright_q=3, dg_base=0.75, dg_amt=0.50, mg_base=0.25, mg_amt=0.55, bg_base=0.06, bg_amt=0.22, filter_decay=8, filter_f=1200, filter_q=3, clip=0.6, cb=6, cm=0.10, lp=7000 |