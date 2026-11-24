# fftechno - synth definitions

Oldschool acid techno, **132 BPM**, A minor. Only drums and a 303.

Three 303 patterns share one template (`acid_303.txt`) but differ in notes, gates,
accents, slides and filter settings:

- `acid_a` - dark and sparse: low notes, rests, filter nearly closed.
- `acid_b` - rolling: mostly 16ths, mid filter, more movement.
- `acid_c` - bright peak: higher notes, more accents, filter more open.

`bar`, `step`, `beat` and `dur` come from `song.md`. `grid` is the 16-step bar
clock. The 303 envelope is gated per step; each accent opens the filter with a
bright/dark crossfade that decays.

sr: 192000
lp: 16000
osr: 48000
grid: floor(mod(t,{{bar}})/{{step}})

## Instruments

| name   | template      | parameters |
|--------|---------------|------------|
| kick   | kick.txt      | amp=0.95, f0=48, sweep=230, rate=58, decay=26, click_amt=0.5, click_f=1400, click_decay=380, sub_amt=0.55, sub_f=45, sub_decay=16, noise_amt=0.28, noise_decay=280, eq_f=58, eq_g=3.5, clip=0.85 |
| clap   | clap.txt      | amp=0.8, decay1=20, tone_amt=0.5, tone_f=180, decay2=26, hp=900, lpc=9000 |
| hat    | hat_step.txt  | amp=0.4, decay=90, hp=7500, gates=1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1, vel=1.0\|0.5\|0.75\|0.5\|1.0\|0.5\|0.75\|0.5\|1.0\|0.5\|0.75\|0.5\|1.0\|0.5\|0.75\|0.5 |
| ohat   | ohat.txt      | amp=0.5, decay=15, hp=6500, off=0.227273, win=0.20 |
| crash  | crash.txt     | amp=0.35, decay=2.2, tone_amt=0.4, f1=4000, f2=6500, tmix=0.7, decay2=1.8, hp=300, period=14.545455 |
| acid_a | acid_303.txt  | amp=0.9, atk=60, decay=7, acc_def=0.4, accents=1.0\|0.4\|0.4\|0\|0.4\|0.4\|0.7\|0.4\|0.9\|0.4\|0.4\|0\|0.4\|0.4\|0.7\|0.4, gates=1\|0\|0\|0\|1\|0\|0\|1\|0\|0\|1\|0\|0\|0\|1\|0, note_def=110, notes=110\|110\|110\|110\|82.41\|82.41\|82.41\|110\|110\|110\|110\|110\|130.81\|130.81\|110\|98, slides=0\|0\|0\|0\|0\|0\|1\|0\|0\|0\|0\|0\|0\|1\|0\|0, slide_rate=16, vib_amt=0.01, vib_f=5.0, hp=50, bright_lp=1400, dark_lp=160, bg_base=0.08, bg_amt=0.22, dg_base=0.92, dg_amt=0.40, filter_decay=10, clip=0.5, cb=6, cm=0.10, filter_f=520, filter_q=4, lp=8000 |
| acid_b | acid_303.txt  | amp=0.9, atk=45, decay=6, acc_def=0.5, accents=1.0\|0.5\|0.5\|0\|0.5\|0.7\|0.9\|0.5\|1.0\|0.5\|0.5\|0\|0.7\|0.5\|0.9\|0.5, gates=1\|1\|1\|0\|1\|1\|1\|1\|1\|1\|1\|0\|1\|1\|1\|1, note_def=110, notes=110\|110\|220\|110\|130.81\|110\|164.81\|196\|110\|110\|220\|110\|174.61\|130.81\|146.83\|110, slides=0\|0\|1\|0\|0\|0\|0\|1\|0\|0\|1\|0\|0\|0\|0\|1, slide_rate=20, vib_amt=0.015, vib_f=5.5, hp=50, bright_lp=2000, dark_lp=220, bg_base=0.10, bg_amt=0.32, dg_base=0.88, dg_amt=0.45, filter_decay=9, clip=0.5, cb=6, cm=0.10, filter_f=850, filter_q=4, lp=9000 |
| acid_c | acid_303.txt  | amp=1.0, atk=35, decay=5, acc_def=0.6, accents=1.0\|0.6\|0.6\|0\|0.8\|0.6\|1.0\|0.6\|1.0\|0.6\|0.6\|0\|0.8\|0.6\|1.0\|0.8, gates=1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1, note_def=110, notes=110\|164.81\|220\|110\|196\|164.81\|261.63\|220\|110\|164.81\|220\|130.81\|196\|261.63\|220\|164.81, slides=0\|1\|0\|0\|1\|0\|0\|1\|0\|1\|0\|0\|1\|0\|1\|0, slide_rate=24, vib_amt=0.02, vib_f=6.0, hp=50, bright_lp=3200, dark_lp=320, bg_base=0.14, bg_amt=0.40, dg_base=0.82, dg_amt=0.45, filter_decay=8, clip=0.55, cb=6, cm=0.10, filter_f=1400, filter_q=5, lp=10000 |