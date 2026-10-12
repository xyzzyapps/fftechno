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
bar: 1.548387
step: 0.096774
beat: 0.387097
gold: 2.399963
vbase: 0.6
vamt: 0.4
grid: floor(mod(t,1.548387)/0.096774)
halfgrid: floor(mod(t,0.774194)/0.096774)
beatgrid: floor(mod(t,1.548387)/0.387097)

## Instruments

| name      | template      | parameters |
|-----------|---------------|------------|
| kick      | kick.txt      | amp=0.95, f0=48, sweep=230, rate=58, decay=26, click_amt=0.5, click_f=1400, click_decay=380, sub_amt=0.55, sub_f=45, sub_decay=16, noise_amt=0.28, noise_decay=280, eq_f=58, eq_g=3.5, clip=0.85 |
| snare     | snare.txt     | amp=0.7, tone_amt=0.7, f1=185, f2=330, tmix=0.6, decay=24, noise_amt=0.9, ndecay=30, hp=180, lpc=8500, gates=0\|0\|0\|0\|1\|0\|0\|0\|0\|0\|0\|0\|1\|0\|0\|0 |
| snarefill | snare.txt     | amp=0.7, tone_amt=0.7, f1=185, f2=330, tmix=0.6, decay=22, noise_amt=0.9, ndecay=26, hp=180, lpc=8500, gates=1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1 |
| clap      | clap.txt      | amp=0.8, decay1=20, tone_amt=0.5, tone_f=180, decay2=26, hp=900, lpc=9000 |
| hat       | hat.txt       | amp=0.55, decay=95, hp=7000, gates=1\|1\|0\|0\|1\|1\|0\|0\|1\|1\|0\|0\|1\|1\|0\|0 |
| ohat      | ohat.txt      | amp=0.6, decay=15, hp=6500, off=0.193548, win=0.18 |
| ride      | ride.txt      | amp=0.45, tone_amt=0.45, f1=3000, f2=4200, tmix=0.7, f3=5400, tmix2=0.5, decay=16, noise_amt=0.5, ndecay=50, hp=1500, lpc=13000, gates=1\|0\|0\|0\|1\|0\|0\|0\|1\|0\|0\|0\|1\|0\|0\|0 |
| crash     | crash.txt     | amp=0.4, decay=2.2, tone_amt=0.4, f1=4000, f2=6500, tmix=0.7, decay2=1.8, hp=300, period=12.387096 |
| breakbeat | breakbeat.txt | amp=0.85, kick_amt=0.9, kf=58, ksweep=140, krate=44, kdecay=30, snare_amt=0.75, snoise=0.9, stone=0.5, sf=200, sdecay=26, hat_amt=0.22, hdecay=55, chop_base=0.72, chop_amt=0.28, chopf=0.096774, hp=250, lpc=7500, kgates=1\|0\|0\|1\|0\|0\|1\|0\|0\|0\|1\|0\|1\|0\|0\|0, sgates=0\|0\|0\|0\|1\|0\|0\|0\|0\|0\|0\|0\|1\|0\|0\|1, hgates=1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|1 |
| shaker    | shaker.txt    | amp=0.7, decay=70, hp=9000, gates=0\|0\|1\|0\|0\|0\|1\|0\|0\|0\|1\|0\|0\|0\|1\|0 |
| conga     | conga.txt     | amp=0.6, sweep=1.25, rate=42, decay=22, hp=200, lpc=6000, a1=0.8, a2=0.5, ad=32, adc=0.14, slap=0.25, slap_decay=90, pitch_def=196, pitches=262\|262\|196\|196\|196\|233\|233\|196\|196\|175\|196\|220\|196\|233\|196\|196, gates=1\|1\|0\|1\|0\|1\|1\|0\|1\|1\|0\|1\|0\|1\|1\|0 |
| reese     | reese.txt     | amp=0.42, decay=0.6, det=0.85, detune=1.008, sub_amt=0.5, hp=28, cut=950, res_g=9, clip=0.7, note_def=55, notes=49\|49\|55\|65.41 |
| acid      | acid.txt      | amp=0.7, decay=5, bend_rate=28, vib_amt=0.03, vib_f=5.5, bright_lp=6000, dark_lp=350, bg_base=0.15, bg_amt=0.85, dg_base=0.9, dg_amt=0.55, eq1_f=650, eq1_g=10, eq2_f=1300, eq2_g=5, res_f=1800, res_q=6, clip=0.55, cb=8, cm=0.35, hp=30, res_eq_f=900, res_eq_g=6, acc_def=0.7, bend_def=0.05, note_def=87.31, gates=1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1, accents=1.0\|0.7\|0.7\|1.0\|0.7\|0.7\|1.0\|0.7\|1.0\|0.7\|0.7\|1.0\|0.7\|0.7\|1.0\|0.7, notes=87.31\|87.31\|174.61\|87.31\|87.31\|87.31\|349.23\|87.31\|87.31\|174.61\|87.31\|87.31\|87.31\|349.23\|174.61\|87.31, bends=0.05\|0.05\|0.35\|0.05\|0.05\|0.05\|0.35\|0.05\|0.05\|0.05\|0.35\|0.05\|0.05\|0.05\|0.35\|0.05 |
| lead_pwm  | lead_pwm.txt  | amp=0.5, decay=12, det=0.6, d1=1.005, d2=0.995, pw_base=0.5, pw_amt=0.3, pw_f=0.7, hp=200, clip=0.6, note_def=392, gates=1\|0\|1\|1\|0\|1\|0\|1\|1\|0\|1\|1\|0\|1\|0\|1, notes=392\|392\|523.25\|392\|349.23\|392\|440\|392\|392\|523.25\|587.33\|523.25\|392\|349.23\|392\|440 |
| lead_fm   | lead_fm.txt   | amp=0.6, decay=14, fm_amt=1.5, ratio=6, det=0.7, d1=1.004, hp=200, ph_speed=0.5, ph_decay=0.4, clip=0.6, note_def=174.61, gates=1\|0\|0\|1\|0\|1\|0\|0\|1\|0\|0\|1\|0\|1\|0\|0, notes=174.61\|174.61\|261.63\|220\|174.61\|220\|261.63\|174.61\|174.61\|261.63\|293.66\|261.63\|174.61\|220\|261.63\|220 |
| pad       | pad.txt       | amp=0.14, base=0.7, amt=0.3, period=8.0, det=0.7, detune=1.004, hp=300, lpc=6000, note_def=174.61, n1=174.61\|174.61\|174.61\|174.61\|174.61\|174.61\|174.61\|174.61\|174.61\|174.61\|174.61\|174.61\|174.61\|174.61\|174.61\|174.61, n2=207.65\|207.65\|207.65\|207.65\|207.65\|207.65\|207.65\|207.65\|207.65\|207.65\|207.65\|207.65\|207.65\|207.65\|207.65\|207.65, n3=261.63\|261.63\|261.63\|261.63\|261.63\|261.63\|261.63\|261.63\|261.63\|261.63\|261.63\|261.63\|261.63\|261.63\|261.63\|261.63 |
| stab      | stab.txt      | amp=0.5, decay=10, det=0.6, detune=1.01, hp=250, lpc=5000, clip=0.7, note_def=261.63, n1=261.63\|261.63\|261.63\|261.63\|261.63\|261.63\|261.63\|261.63\|261.63\|261.63\|261.63\|261.63\|261.63\|261.63\|261.63\|261.63, n2=311.13\|311.13\|311.13\|311.13\|311.13\|311.13\|311.13\|311.13\|311.13\|311.13\|311.13\|311.13\|311.13\|311.13\|311.13\|311.13, gates=1\|0\|0\|0\|0\|0\|1\|0\|0\|0\|1\|0\|0\|0\|0\|0 |
