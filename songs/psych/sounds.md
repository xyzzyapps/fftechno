# fftechno - synth definitions

Psychedelic 1960s rock, wall of sound, no samples. All sound is `aevalsrc`; the
"wall" is two detuned fuzz guitars panned wide, a Farfisa-ish organ chord, a
mellotron pad and tambourine, plus a fuzz lead. Heavy reverb is in `song.md`
(`reverb_seconds: 5.5`, `reverb_send: 0.60`).

New templates: `guitar_fuzz.txt` (power-chord wall: root/fifth/octave + detuned
pairs, tanh fuzz, cabinet EQ, phaser), `guitar_lead.txt` (fuzz lead with vibrato +
phaser + slap), `organ.txt` (square-wave drawbars, tremolo + chorus),
`bass_rock.txt` (gated electric bass with grit), `tamb.txt` (noise + jingle). The
drums reuse `kick_trip.txt`, `snare.txt`, `tom.txt`, `hat_step.txt`, `ride.txt`,
`crash.txt`; the wash reuses `pad.txt`.

`bar`, `step`, `beat` and `dur` come from `song.md`. `grid` is a 16-step clock.

sr: 96000
osr: 48000
grid: floor(mod(t,{{bar}})/{{step}})

## Instruments

| name     | template        | parameters |
|----------|-----------------|------------|
| kick     | kick_trip.txt   | amp=1.0, f0=55, sweep=180, rate=45, decay=9, click_amt=0.45, click_f=1800, click_decay=300, sub_amt=0.7, sub_f=50, sub_decay=10, noise_amt=0.2, noise_decay=250, eq_f=70, eq_g=3, clip=0.8, lp=12000, gates=1\|0\|0\|0\|0\|0\|1\|0\|1\|0\|0\|0\|0\|0\|0\|0 |
| snare    | snare.txt       | amp=0.8, tone_amt=0.5, f1=190, f2=330, tmix=0.6, decay=18, noise_amt=0.9, ndecay=22, hp=150, lpc=7000, lp=9000, gates=0\|0\|0\|0\|1\|0\|0\|0\|0\|0\|0\|0\|1\|0\|0\|0 |
| tom      | tom.txt         | amp=0.9, sweep=0.6, rate=30, decay=8, hp=60, lpc=4000, a1=0.8, a2=0.4, ad=40, adc=0.3, lp=8000, vbase=0.8, vamt=0.2, gold=1.7, pitches=196\|196\|164.8\|164.8\|146.8\|146.8\|130.8\|130.8\|110\|110\|98\|98\|87.3\|87.3\|82.4\|82.4, pitch_def=196, gates=1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0 |
| hat      | hat_step.txt    | amp=0.5, decay=40, hp=6000, lp=16000, gates=1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0, vel=1\|1\|0.7\|1\|1\|1\|0.7\|1\|1\|1\|0.7\|1\|1\|1\|0.7\|1 |
| ride     | ride.txt        | amp=0.4, tone_amt=0.4, f1=3200, tmix=0.5, f2=4700, tmix2=0.4, f3=6300, decay=22, noise_amt=0.6, ndecay=25, hp=3000, lpc=12000, lp=16000, gates=1\|0\|0\|0\|1\|0\|0\|0\|1\|0\|0\|0\|1\|0\|0\|0 |
| crash    | crash.txt       | amp=0.55, decay=1.2, tone_amt=0.3, f1=4200, tmix=0.5, f2=6800, decay2=1.5, period=17.4545, hp=2500, lp=18000 |
| tamb     | tamb.txt        | amp=0.6, noise_amt=0.8, decay=60, tone_amt=0.3, f1=7000, tmix=0.4, f2=9500, decay2=80, hp=5000, lp=16000, gates=1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0 |
| bass     | bass_rock.txt   | amp=1.0, decay=4.0, sub=0.6, hp=35, lp_bass=900, lp_q=1.0, eq_f=90, eq_g=4, clip=0.7, lp=5000, gates=1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0, notes=82.41\|82.41\|82.41\|82.41\|98\|98\|98\|98\|110\|110\|110\|110\|123.47\|123.47\|146.83\|146.83, note_def=82.41 |
| gtr_l    | guitar_fuzz.txt | amp=1.0, decay=1.2, oct=0.55, fifth=0.7, det=0.5, detune=1.003, det2=0.35, detune2=0.997, hp=90, clip=0.55, lpc=6000, eq_f=1200, eq_g=4, ph_speed=0.30, lp=9000, a1=0.8, a2=0.45, ad=70, adc=0.25, gates=1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0, notes=82.41\|82.41\|82.41\|82.41\|98\|98\|98\|98\|110\|110\|110\|110\|123.47\|123.47\|146.83\|146.83, note_def=82.41 |
| gtr_r    | guitar_fuzz.txt | amp=1.0, decay=1.2, oct=0.55, fifth=0.7, det=0.5, detune=0.997, det2=0.35, detune2=1.003, hp=90, clip=0.55, lpc=6000, eq_f=1350, eq_g=3.5, ph_speed=0.45, lp=9000, a1=0.8, a2=0.45, ad=70, adc=0.25, gates=1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0, notes=82.41\|82.41\|82.41\|82.41\|98\|98\|98\|98\|110\|110\|110\|110\|123.47\|123.47\|146.83\|146.83, note_def=82.41 |
| gtr_lead | guitar_lead.txt | amp=0.5, decay=1.8, sub=0.35, oct=0.4, hp=200, clip=0.5, lpc=7000, vibf=5.5, vibd=0.35, eq_f=1500, eq_g=3, lp=10000, gates=1\|0\|0\|0\|1\|0\|0\|0\|1\|0\|0\|0\|1\|1\|0\|0, notes=164.81\|164.81\|196\|220\|246.94\|246.94\|220\|196\|164.81\|164.81\|196\|220\|246.94\|293.66\|329.63\|293.66, note_def=164.81 |
| organ    | organ.txt       | amp=0.18, h1=0.5, h2=0.35, h3=0.25, hp=180, lp=7000, tremf=6.5, tremd=0.35, clip=0.7, gates=1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1, n1=164.81\|164.81\|164.81\|164.81\|164.81\|164.81\|164.81\|164.81\|146.83\|146.83\|146.83\|146.83\|146.83\|146.83\|146.83\|146.83, n2=196\|196\|196\|196\|196\|196\|196\|196\|185\|185\|185\|185\|185\|185\|185\|185, n3=246.94\|246.94\|246.94\|246.94\|246.94\|246.94\|246.94\|246.94\|220\|220\|220\|220\|220\|220\|220\|220, note_def=164.81 |
| pad      | pad.txt         | amp=0.06, base=0.7, amt=0.3, period=8, det=0.3, detune=1.004, hp=200, lpc=5000, lp=9000, n1=329.63\|329.63\|329.63\|329.63\|329.63\|329.63\|329.63\|329.63\|293.66\|293.66\|293.66\|293.66\|293.66\|293.66\|293.66\|293.66, n2=391.99\|391.99\|391.99\|391.99\|391.99\|391.99\|391.99\|391.99\|369.99\|369.99\|369.99\|369.99\|369.99\|369.99\|369.99\|369.99, n3=493.88\|493.88\|493.88\|493.88\|493.88\|493.88\|493.88\|493.88\|440\|440\|440\|440\|440\|440\|440\|440, note_def=329.63 |
