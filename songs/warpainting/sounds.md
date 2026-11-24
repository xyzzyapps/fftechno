# fftechno - synth definitions

Original psychedelic drone rock inspired by The Myrrors' "Warpainting":
**79 BPM**, B minor, 8:00. A slow hypnotic jam: two detuned fuzz guitars drone a
B/F# riff with G colour, organ and pad hold Bm | Gmaj7 | Bm | G, the bass moves
B -> G, and the drums are sparse and tom-heavy. A wah fuzz lead enters later.
Heavy 6 s reverb is in `song.md`.

`bar`, `step`, `beat` and `dur` come from `song.md`. `grid` is the 16-step bar
clock; `chordgrid` is one chord every two bars over 8 bars.

sr: 96000
lp: 16000
osr: 48000
gold: 1.7
vbase: 0.8
vamt: 0.2
grid: floor(mod(t,{{bar}})/{{step}})
chordgrid: floor(mod(t,{{bar}}*8)/({{bar}}*2))

## Instruments

| name     | template        | parameters |
|----------|-----------------|------------|
| kick     | kick_trip.txt   | amp=1.0, f0=55, sweep=180, rate=45, decay=9, click_amt=0.45, click_f=1800, click_decay=300, sub_amt=0.7, sub_f=50, sub_decay=10, noise_amt=0.2, noise_decay=250, eq_f=70, eq_g=3, clip=0.8, lp=12000, gates=1\|0\|0\|0\|0\|0\|1\|0\|1\|0\|0\|0\|0\|0\|0\|0 |
| snare    | snare.txt       | amp=0.8, tone_amt=0.5, f1=190, f2=330, tmix=0.6, decay=18, noise_amt=0.9, ndecay=22, hp=150, lpc=7000, lp=9000, gates=0\|0\|0\|0\|1\|0\|0\|0\|0\|0\|0\|0\|1\|0\|0\|0 |
| tom      | tom.txt         | amp=0.9, sweep=0.6, rate=30, decay=8, hp=60, lpc=4000, a1=0.8, a2=0.4, ad=40, adc=0.3, lp=8000, vbase=0.8, vamt=0.2, gold=1.7, pitch_def=123.47, pitches=123.47\|123.47\|110\|110\|98\|98\|92.5\|92.5\|82.4\|82.4\|73.42\|73.42\|61.74\|61.74\|55\|55, gates=1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0 |
| hat      | hat_step.txt    | amp=0.5, decay=40, hp=6000, lp=16000, gates=1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0, vel=1\|1\|0.7\|1\|1\|1\|0.7\|1\|1\|1\|0.7\|1\|1\|1\|0.7\|1 |
| ride     | ride.txt        | amp=0.4, tone_amt=0.4, f1=3200, tmix=0.5, f2=4700, tmix2=0.4, f3=6300, decay=22, noise_amt=0.6, ndecay=25, hp=3000, lpc=12000, lp=16000, gates=1\|0\|0\|0\|1\|0\|0\|0\|1\|0\|0\|0\|1\|0\|0\|0 |
| crash    | crash.txt       | amp=0.55, decay=1.2, tone_amt=0.3, f1=4200, tmix=0.5, f2=6800, decay2=1.5, period=48.607595, hp=2500, lp=18000 |
| tamb     | tamb.txt        | amp=0.6, noise_amt=0.8, decay=60, tone_amt=0.3, f1=7000, tmix=0.4, f2=9500, decay2=80, hp=5000, lp=16000, gates=1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0 |
| bass     | bass_rock.txt   | amp=1.0, decay=0.6, sub=0.6, hp=35, lp_bass=900, lp_q=1.0, eq_f=90, eq_g=4, clip=0.7, lp=5000, grid={{chordgrid}}, gates=1\|1\|1\|1, note_def=61.74, notes=61.74\|49\|61.74\|49 |
| gtr_l    | guitar_fuzz.txt | amp=1.0, decay=1.2, oct=0.55, fifth=0.7, det=0.5, detune=1.003, det2=0.35, detune2=0.997, hp=90, clip=0.55, lpc=6000, eq_f=1200, eq_g=4, ph_speed=0.30, lp=9000, a1=0.8, a2=0.45, ad=70, adc=0.25, gates=1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1, note_def=123.47, notes=123.47\|123.47\|185\|123.47\|196\|123.47\|146.83\|123.47\|123.47\|123.47\|185\|123.47\|196\|185\|146.83\|123.47 |
| gtr_r    | guitar_fuzz.txt | amp=1.0, decay=1.2, oct=0.55, fifth=0.7, det=0.5, detune=0.997, det2=0.35, detune2=1.003, hp=90, clip=0.55, lpc=6000, eq_f=1350, eq_g=3.5, ph_speed=0.45, lp=9000, a1=0.8, a2=0.45, ad=70, adc=0.25, gates=1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1, note_def=123.47, notes=123.47\|123.47\|185\|123.47\|196\|123.47\|146.83\|123.47\|123.47\|123.47\|185\|123.47\|196\|185\|146.83\|123.47 |
| gtr_lead | guitar_wah.txt  | amp=0.5, decay=1.8, sub=0.35, oct=0.4, hp=200, clip=0.5, lpc=7000, ph_speed=0.4, eq_f=1500, eq_g=3, lp=10000, gates=1\|0\|0\|1\|0\|0\|1\|0\|0\|1\|0\|0\|1\|0\|1\|0, note_def=246.94, notes=246.94\|246.94\|293.66\|329.63\|369.99\|369.99\|440\|369.99\|329.63\|293.66\|246.94\|246.94\|293.66\|329.63\|369.99\|440 |
| organ    | organ.txt       | amp=0.18, h1=0.5, h2=0.35, h3=0.25, hp=180, lp=7000, tremf=6.5, tremd=0.35, clip=0.7, grid={{chordgrid}}, gates=1\|1\|1\|1, note_def=246.94, n1=246.94\|196\|246.94\|196, n2=293.66\|246.94\|293.66\|246.94, n3=369.99\|369.99\|369.99\|293.66 |
| pad      | pad.txt         | amp=0.06, base=0.7, amt=0.3, period=8, det=0.3, detune=1.004, hp=200, lpc=5000, lp=9000, grid={{chordgrid}}, note_def=246.94, n1=246.94\|196\|246.94\|196, n2=293.66\|246.94\|293.66\|246.94, n3=369.99\|369.99\|369.99\|293.66 |