# fftechno - synth definitions

Scratch song: an 8-bar **beat sketch** (88 BPM). It is the synthesized break
(`break_synth.txt`) plus an electronic kick and a gated bass. The 4-minute
`triphop` song does not copy this file. That song uses `break_sp.txt` and `sub.txt`.

The break is **synthesized, no samples**: a swept kick + tone/noise snare + noise
hat, each with its own 2-bar gate and velocity list (so ghost notes are just low
velocities), played on a **swung** clock and finished lo-fi (band-limited,
saturated, bit-reduced) so it reads as a sampled break.

`sp` is the swung phase: the odd 16ths start `swd` of a step late (a pairing warp),
while the gates stay on the straight `bgrid`.

`bar`, `step`, `beat` and `dur` come from `song.md`.

sr: 192000
lp: 19000
osr: 48000
grid: floor(mod(t,{{bar}})/{{step}})
bgrid: floor(mod(t,{{bar}}*2)/{{step}})
sp: mod(mod(mod(t,{{bar}}*2)/{{step}},1)-0.14*mod(floor(mod(t,{{bar}}*2)/{{step}}),2),1)

## Instruments

| name  | template        | parameters |
|-------|-----------------|------------|
| kick  | kick_trip.txt   | amp=0.95, f0=46, sweep=200, rate=52, decay=22, click_amt=0.4, click_f=1200, click_decay=380, sub_amt=0.6, sub_f=44, sub_decay=15, noise_amt=0.25, noise_decay=270, eq_f=55, eq_g=3.5, clip=0.85, gates=1\|0\|0\|0\|0\|0\|1\|0\|0\|0\|1\|0\|0\|0\|1\|0 |
| break | break_synth.txt | amp=0.9, kf=62, ksweep=90, krate=40, kdecay=30, kclick=0.25, kcd=200, stone=0.5, sf=190, sdecay=22, snoise=0.9, snd=28, hdecay=70, hp=180, eq_f=2500, eq_w=1.0, eq_g=4, clip=0.8, bits=10, cmix=0.25, lpc=8000, kgates=1\|0\|0\|0\|0\|0\|1\|0\|0\|0\|1\|0\|1\|0\|0\|0\|1\|0\|0\|0\|0\|0\|1\|0\|1\|0\|0\|0\|0\|0\|0\|0, kvel=1\|1\|1\|1\|1\|1\|0.35\|1\|1\|1\|0.85\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|0.3\|1\|0.9\|1\|1\|1\|1\|1\|1\|1, sgates=0\|0\|0\|0\|1\|0\|0\|1\|0\|0\|0\|0\|1\|0\|0\|1\|0\|0\|0\|0\|1\|0\|0\|0\|0\|0\|0\|0\|1\|1\|1\|1, svel=1\|1\|1\|1\|1\|1\|1\|0.35\|1\|1\|1\|1\|1\|1\|1\|0.3\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|0.35\|0.55\|0.8, hgates=1\|0\|1\|0\|1\|1\|1\|0\|1\|0\|1\|0\|1\|1\|1\|0\|1\|0\|1\|0\|1\|1\|1\|0\|1\|0\|1\|0\|1\|1\|1\|0, hvel=1.0\|1\|0.65\|1\|1.0\|0.45\|0.65\|1\|1.0\|1\|0.65\|1\|1.0\|0.45\|0.65\|1\|1.0\|1\|0.65\|1\|1.0\|0.45\|0.65\|1\|1.0\|1\|0.65\|1\|1.0\|0.45\|0.65\|1 |
| bass  | bass_gate.txt   | amp1=0.5, amp2=0.42, amp3=0.3, decay1=15, decay2=12, detune=1.003, note_def=73.42, lp_bass=300, lp_q=1.3, eq_f=50, eq_g=5, sub_cut=70, sub_boost=7, sub_dry=0.5, sub_wet=1, clip=0.85, gates=1\|0\|0\|1\|0\|0\|1\|0\|1\|0\|0\|1\|0\|0\|1\|0, notes=73.42\|73.42\|73.42\|73.42\|87.31\|87.31\|87.31\|87.31\|98\|98\|98\|98\|110\|110\|110\|110 |
