# fftechno - synth definitions

`python -m fftechno synth` renders each instrument below into `filters/<name>.txt`
by plugging these values into `templates/<template>`. There are no defaults: every
placeholder an instrument uses must be defined by the globals here or its own
`parameters`.

Scalar values are single tokens. List values (used by `{{if_steps(...)}}`) are
`\|`-separated inside the table cell (the backslash escapes the markdown pipe).

sr: 192000
dur: 240
lp: 19000
osr: 48000
bar: 1.714286
step: 0.107143
gold: 2.399963
vbase: 0.6
vamt: 0.4
grid: floor(mod(t,1.714286)/0.107143)
halfgrid: floor(mod(t,0.857143)/0.107143)
note_grid: floor(t/0.18)

## Instruments

| name   | template    | parameters |
|--------|-------------|------------|
| kick   | kick.txt    | amp=0.95, beat=0.428571, f0=48, sweep=220, rate=55, decay=24, click_amt=0.4, click_f=1200, click_decay=420, sub_amt=0.5, sub_f=45, sub_decay=18, noise_amt=0.3, noise_decay=300, eq_f=60, eq_g=3, clip=0.8 |
| clap   | clap.txt    | amp=0.55, beat=0.428571, decay1=20, tone_amt=0.5, tone_f=200, decay2=28, hp=900, lpc=9000 |
| hat    | hat.txt     | amp=0.35, decay=95, hp=7000 |
| ohat   | ohat.txt    | amp=0.4, decay=15, hp=6500, off=0.214286, beat=0.428571, win=0.20 |
| perc   | tom.txt     | amp=0.7, sweep=1.1, rate=28, decay=16, hp=110, lpc=3500, a1=0.8, a2=0.7, ad=55, adc=0.25, pitch_def=147, pitches=196\|196\|147\|147\|147\|175\|175\|147\|147\|131\|147\|165\|147\|175\|147\|147, gates=1\|1\|0\|1\|0\|1\|1\|0\|1\|1\|0\|1\|0\|1\|1\|0 |
| bongo  | tom.txt     | amp=0.5, sweep=1.1, rate=30, decay=20, hp=150, lpc=5000, a1=0.8, a2=0.7, ad=40, adc=0.2, pitch_def=262, pitches=262\|262\|330\|262\|262\|262\|262\|392\|262\|262\|294\|262\|349\|262\|262\|262, gates=0\|0\|1\|0\|1\|0\|0\|1\|0\|0\|1\|0\|1\|0\|0\|1 |
| rim    | rim.txt     | amp=0.4, n_amt=0.5, tone_f=1500, decay=120, hp=1500, gates=0\|1\|0\|0\|0\|1\|0\|0\|0\|1\|0\|0\|0\|1\|0\|0 |
| shaker | shaker.txt  | amp=0.28, decay=70, hp=9000, gates=0\|0\|1\|0\|0\|0\|1\|0\|0\|0\|1\|0\|0\|0\|1\|0 |
| bass   | bass.txt    | amp1=0.55, amp2=0.4, amp3=0.32, decay1=14, decay2=10, detune=1.006, note_def=49, notes=55\|55\|55\|55\|55\|55\|110\|55\|49\|49\|49\|49\|49\|49\|98\|49, lp_bass=1600, eq_f=45, eq_g=5, sub_cut=60, sub_boost=6, sub_dry=0.6, sub_wet=1, clip=0.85 |
| acid   | acid.txt    | amp=0.7, decay=5, gate_def=0.75, gates=1.0\|0.75\|0.75\|0\|0.75\|0.75\|1.0\|0.75\|1.0\|0.75\|0.75\|0\|0.75\|0.75\|1.0\|0.75, note_def=110, notes=110\|110\|220\|110\|130.81\|110\|164.81\|196\|110\|110\|220\|110\|174.61\|130.81\|146.83\|110, bend_def=0.05, bends=0.05\|0.05\|0.35\|0.05\|0.05\|0.05\|0.05\|0.35\|0.05\|0.05\|0.35\|0.05\|0.05\|0.05\|0.05\|0.35, bend_rate=28, vib_amt=0.03, vib_f=5.5, bright_lp=5000, dark_lp=350, bg_base=0.20, bg_amt=0.80, dg_base=0.90, dg_amt=0.50, sweep_period=16, eq1_f=650, eq1_g=11, eq2_f=1300, eq2_g=6, res_f=1600, res_q=5, clip=0.55, cb=8, cm=0.35 |
| growl  | growl.txt   | amp=0.85, swin=0.070, gp=0.063, gd=0.046, go1=0.063, go2=0.047, go3=0.032, go4=0.016, c1=0.6, c2=0.4, f0=65, fm_amt=1.5, fm_f=12, phrase_def=1.00, phrase=1.00\|1.19\|1.08\|1.00\|0.84\|0.75\|1.12\|1.00, gate_def=1, gates=1\|1\|1\|0\|1\|1\|1\|0, r_base=0.6, r_amt=0.4, r_f=173, e1f=380, e1g=8, e2f=1100, e2g=7, e3f=2600, e3g=6, cb=7, cm=0.5, clip=0.7, gp_lp=7000 |
| beeps  | beeps.txt   | amp=0.5, p2=0.4, ratio=2.76, decay=7, notelen=0.18, ncount=5, note_def=1318.51, notes=523.25\|659.25\|783.99\|1046.5\|1318.51, beep_dur=1.3, d0=500, d1=68000, d2=137000, tlp=12000, ae1=0.8, ae2=0.7, ae3=80\|160, ae4=0.4\|0.2 |
