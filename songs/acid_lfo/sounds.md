# fftechno - synth definitions

30-second TB-303 loop with continuous, LFO-driven movement.

## Attribution

The 303 pattern is **"Acid Tabs 200"** from
[acid-tabs.com](https://acid-tabs.com/303_patterns.php?Pattern_Select=QWNpZCBUYWJzIDIwMCAtIFRCLTMwMyBQYXR0ZXJu):

- Pattern by **J.McConaghy / Acid-Tabs.com**
- Licensed **CC BY-SA**
- 130 BPM, square wave, minor scale

Only the pitch/accent/slide/gate pattern is used; the movement below is original.

## The pattern (exact)

| Step | Hz | Accent | Slide | Gate |
|---|---|---|---|---|
| 1 | 246.94 | 1.0 | 0 | 1 |
| 2 | 123.47 | 0.5 | 1 | 1 |
| 3 | 246.94 | 0.5 | 0 | 1 |
| 4 | 123.47 | 1.0 | 0 | 1 |
| 5 | 293.66 | 1.0 | 0 | 1 |
| 6 | 185.00 | 1.0 | 0 | 1 |
| 7 | 246.94 | 1.0 | 0 | 1 |
| 8 | 246.94 | 0.5 | 0 | 1 |
| 9 | 246.94 | 0.5 | 0 | 1 |
| 10 | 783.99 | 1.0 | 0 | 1 |
| 11 | 246.94 | 1.0 | 0 | 0 |
| 12 | 246.94 | 1.0 | 0 | 1 |
| 13 | 220.00 | 0.5 | 1 | 1 |
| 14 | 587.33 | 0.5 | 0 | 1 |
| 15 | 277.18 | 0.5 | 0 | 1 |
| 16 | 146.83 | 0.5 | 0 | 1 |

## How the movement works

`acid_lfo.txt` splits the oscillator into **four static resonant low-passes**
(320 / 700 / 1500 / 3200 Hz). Each is faded with its own slow sine:

```text
volume = w_a + w_b * sin(2*PI*t / r + p)
```

- `r` is the LFO period in seconds; the four bands use different, non-matching
  rates, so they never line up.
- `p` is a phase offset, which staggers the bands.
- a final master LFO (`sw_a`, `sw_b`, `sw_r`) breathes the overall 303 level.

Because the bands crossfade at different rates, the sound continuously shifts from
dark and closed to bright and open - a slow knob twist - while the notes stay
identical. Everything is deterministic: `volume` with `eval=frame` is evaluated
per frame from `t`.

`lowpass=f` cannot be time-varying in ffmpeg, which is why the filter movement is a
crossfade between fixed filters rather than a swept cutoff.

## Instruments

`bar`, `step`, `beat` and `dur` come from `song.md`. `grid` is the 16-step clock.

sr: 192000
lp: 16000
osr: 48000
grid: floor(mod(t,{{bar}})/{{step}})

| name | template      | parameters |
|------|---------------|------------|
| kick | kick.txt      | amp=0.95, f0=48, sweep=230, rate=58, decay=26, click_amt=0.5, click_f=1400, click_decay=380, sub_amt=0.55, sub_f=45, sub_decay=16, noise_amt=0.28, noise_decay=280, eq_f=58, eq_g=3.5, clip=0.85 |
| clap | clap.txt      | amp=1.0, decay1=26, tone_amt=0.65, tone_f=200, decay2=42, hp=700, lpc=11000 |
| hat  | hat_step.txt  | amp=0.4, decay=90, hp=7500, gates=1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1, vel=1.0\|0.5\|0.75\|0.5\|1.0\|0.5\|0.75\|0.5\|1.0\|0.5\|0.75\|0.5\|1.0\|0.5\|0.75\|0.5 |
| sub  | sub_bounce.txt | amp=0.5, atk=90, dec=9, harm=0.18, note_def=55, gates=1\|0\|0\|1\|0\|0\|1\|0\|1\|0\|0\|1\|0\|0\|1\|0, notes=55\|55\|55\|55\|55\|55\|55\|55\|61.74\|61.74\|61.74\|61.74\|61.74\|61.74\|61.74\|61.74, hp=30, lp_bass=120, lp_q=0.7, eq_f=50, eq_g=5, sub_cut=60, sub_boost=6, sub_dry=0.5, sub_wet=1, clip=0.85, lp=6000 |
| acid | acid_lfo.txt  | amp=1.0, atk=35, dec=5, acc_def=0.6, accents=1.0\|0.5\|0.5\|1.0\|1.0\|1.0\|1.0\|0.5\|0.5\|1.0\|1.0\|1.0\|0.5\|0.5\|0.5\|0.5, gates=1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|0\|1\|1\|1\|1\|1, note_def=246.94, notes=246.94\|123.47\|246.94\|123.47\|293.66\|185\|246.94\|246.94\|246.94\|783.99\|246.94\|246.94\|220\|587.33\|277.18\|146.83, slides=0\|1\|0\|0\|0\|0\|0\|0\|0\|0\|0\|0\|1\|0\|0\|0, slide_rate=24, vib_amt=0.015, vib_f=5.5, square=0.65, hp=50, f1=320, q1=3.5, f2=700, q2=3, f3=1500, q3=2.5, f4=3200, q4=2, w1a=0.34, w1b=0.30, r1=7.3, p1=0, w2a=0.30, w2b=0.28, r2=11.9, p2=1.2, w3a=0.20, w3b=0.20, r3=17.3, p3=2.4, w4a=0.08, w4b=0.16, r4=23.7, p4=3.6, sw_a=0.88, sw_b=0.14, sw_r=13.1, clip=0.5, lp=7000 |