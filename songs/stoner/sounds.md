# fftechno - synth definitions

Stoner rock, no samples. A hypnotic drop-D fuzz riff (two detuned guitars panned
wide), a thick fuzz bass, big sparse drums, a wah-ish fuzz lead and a low organ
drone in the intro/breakdown. Heavy room in `song.md` (`reverb_seconds: 5.0`).

Reuses `guitar_fuzz.txt`, `guitar_lead.txt`-family fuzz, `bass_rock.txt`, `organ.txt`
and the drum templates. `guitar_wah.txt` is new: a single-note fuzz lead with a
phaser (no vibrato/echo, which grew unstable together over 4 minutes).

`bar`, `step`, `beat` and `dur` come from `song.md`. `grid` is a 16-step clock.

sr: 96000
osr: 48000
grid: floor(mod(t,{{bar}})/{{step}})

## Instruments

| name     | template        | parameters |
|----------|-----------------|------------|
| kick     | kick_trip.txt   | amp=1.0, f0=50, sweep=200, rate=40, decay=12, click_amt=0.5, click_f=1500, click_decay=280, sub_amt=0.8, sub_f=48, sub_decay=12, noise_amt=0.25, noise_decay=240, eq_f=65, eq_g=4, clip=0.75, lp=10000, gates=1\|0\|0\|0\|0\|0\|1\|0\|1\|0\|0\|0\|0\|0\|0\|0 |
| snare    | snare.txt       | amp=0.9, tone_amt=0.4, f1=180, f2=320, tmix=0.6, decay=22, noise_amt=0.9, ndecay=26, hp=150, lpc=6000, lp=8000, gates=0\|0\|0\|0\|1\|0\|0\|0\|0\|0\|0\|0\|1\|0\|0\|0 |
| tom      | tom.txt         | amp=0.9, sweep=0.6, rate=28, decay=10, hp=55, lpc=3500, a1=0.8, a2=0.4, ad=50, adc=0.3, lp=7000, vbase=0.8, vamt=0.2, gold=1.6, pitches=196\|196\|164.8\|164.8\|146.8\|146.8\|130.8\|130.8\|110\|110\|98\|98\|87.3\|87.3\|82.4\|82.4, pitch_def=196, gates=1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0 |
| hat      | hat_step.txt    | amp=0.3, decay=35, hp=6000, lp=14000, gates=1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0, vel=1\|1\|0.6\|1\|1\|1\|0.6\|1\|1\|1\|0.6\|1\|1\|1\|0.6\|1 |
| ride     | ride.txt        | amp=0.28, tone_amt=0.4, f1=3200, tmix=0.5, f2=4700, tmix2=0.4, f3=6300, decay=24, noise_amt=0.6, ndecay=26, hp=3000, lpc=12000, lp=15000, gates=1\|0\|0\|0\|1\|0\|0\|0\|1\|0\|0\|0\|1\|0\|0\|0 |
| crash    | crash.txt       | amp=0.5, decay=1.5, tone_amt=0.3, f1=4200, tmix=0.5, f2=6800, decay2=1.8, period=25.263, hp=2500, lp=18000 |
| bass     | bass_rock.txt   | amp=1.0, decay=1.4, sub=0.7, hp=30, lp_bass=700, lp_q=1.1, eq_f=70, eq_g=5, clip=0.6, lp=4000, gates=1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0, notes=73.42\|73.42\|73.42\|73.42\|87.31\|87.31\|98\|98\|73.42\|73.42\|73.42\|73.42\|87.31\|87.31\|110\|110, note_def=73.42 |
| gtr_l    | guitar_fuzz.txt | amp=1.2, decay=0.6, oct=0.5, fifth=0.6, det=0.4, detune=1.004, det2=0.3, detune2=0.996, hp=55, clip=0.55, lpc=5000, eq_f=900, eq_g=5, ph_speed=0.18, lp=7000, a1=1.0, a2=1.0, ad=90, adc=0.1, gates=1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0, notes=73.42\|73.42\|73.42\|73.42\|87.31\|87.31\|98\|98\|73.42\|73.42\|73.42\|73.42\|87.31\|87.31\|110\|110, note_def=73.42 |
| gtr_r    | guitar_fuzz.txt | amp=1.2, decay=0.6, oct=0.5, fifth=0.6, det=0.4, detune=0.996, det2=0.3, detune2=1.004, hp=55, clip=0.55, lpc=5000, eq_f=1000, eq_g=4.5, ph_speed=0.25, lp=7000, a1=1.0, a2=1.0, ad=90, adc=0.1, gates=1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0, notes=73.42\|73.42\|73.42\|73.42\|87.31\|87.31\|98\|98\|73.42\|73.42\|73.42\|73.42\|87.31\|87.31\|110\|110, note_def=73.42 |
| gtr_lead | guitar_wah.txt  | amp=0.6, decay=2.0, sub=0.4, oct=0.3, hp=250, clip=0.5, lpc=6000, ph_speed=0.15, eq_f=1400, eq_g=3, lp=9000, gates=1\|0\|0\|0\|1\|0\|0\|0\|1\|0\|0\|0\|1\|0\|0\|0, notes=146.83\|146.83\|174.61\|174.61\|196\|196\|196\|196\|220\|220\|220\|220\|261.63\|261.63\|293.66\|293.66, note_def=146.83 |
| organ    | organ.txt       | amp=0.12, h1=0.5, h2=0.3, h3=0.2, hp=200, lp=5000, tremf=4.5, tremd=0.3, clip=0.8, gates=1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1, n1=146.83\|146.83\|146.83\|146.83\|146.83\|146.83\|146.83\|146.83\|146.83\|146.83\|146.83\|146.83\|146.83\|146.83\|146.83\|146.83, n2=174.61\|174.61\|174.61\|174.61\|174.61\|174.61\|174.61\|174.61\|174.61\|174.61\|174.61\|174.61\|174.61\|174.61\|174.61\|174.61, n3=220\|220\|220\|220\|220\|220\|220\|220\|220\|220\|220\|220\|220\|220\|220\|220, note_def=146.83 |
