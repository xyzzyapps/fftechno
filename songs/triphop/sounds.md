# fftechno - synth definitions

`python -m fftechno synth` renders each instrument below into `filters/triphop/`
by plugging these values into `templates/<template>`. `bar`, `step`, `beat` and
`dur` come from `song.md`. Every other placeholder must be defined by the globals
here or by the instrument's `parameters`.

Scalar values are single tokens. List values (used by `{{if_steps(...)}}`) are
`\|`-separated inside the table cell (the backslash escapes the markdown pipe).

Instrumental trip hop at 84 BPM, in D minor, built like a DJ Shadow / DJ Krush
record rather than a techno kit with a sax lead.

The drum backbone is one **swung, bit-reduced break** (`brk`, an SP-1200-style
chop: short kicks, backbeat snare, ghost notes, closed hats, two lazy open hats).
A separate **boom** (`kick`) rings on beat 1 and the "&" of 2 only, so the low
end is a real kick and the break stays in the midrange. `roll` is a rising snare
fill on the last two beats of every 8 bars.

Harmony is an 8-bar loop: Dm9, Gm9, Bbmaj7, A7. `sub` holds one note for two
bars. `ep` is a dusty FM electric piano, one soft attack per bar. `strings` is a
dark bed on the same chords. `bell` is a sparse pentatonic hook (it rests while
the fill plays). `stab` is one high chord chop per two bars, thrown through a
dotted-eighth dub delay. `horn` holds two long notes per phrase. `rise` is a
dark reversed swell into each phrase. `vinyl` is the dust.

`sp` delays the odd 16ths by 0.22 of a step (about 61% swing). `bgrid` is the
straight 2-bar clock the gates read, so the swing moves the hit, not the pattern.
Those clocks use `{{bar}}`, `{{step}}` and `{{beat}}` from `song.md`.

sr: 192000
lp: 16000
osr: 48000
bgrid: floor(mod(t,{{bar}}*2)/{{step}})
sp: mod(mod(mod(t,{{bar}}*2)/{{step}},1)-0.22*mod(floor(mod(t,{{bar}}*2)/{{step}}),2),1)
cstep: {{bar}}*2
cgrid: floor(mod(t,{{bar}}*8)/{{cstep}})
barstep: {{bar}}
bargrid: floor(mod(t,{{bar}}*8)/{{bar}})
mgrid: floor(mod(t,{{bar}}*8)/{{beat}})
window: {{beat}}*2
local: mod(t,{{bar}}*8)-({{bar}}*8-{{window}})
ph: mod(t,{{bar}}*8)/({{bar}}*8)
ts: if(lt(mod(t,{{bar}}),{{step}}*6),mod(t,{{bar}}),mod(t,{{bar}})-{{step}}*6)

## Instruments

| name    | template      | parameters |
|---------|---------------|------------|
| kick    | boom.txt      | amp=0.62, f0=42, sweep=150, rate=70, decay=6.5, click_amt=0.12, click_f=1400, click_decay=400, sub_amt=0, sub_f=40, sub_decay=8, noise_amt=0.28, noise_decay=90, eq_f=55, eq_g=2, clip=0.9 |
| brk     | break_sp.txt  | amp=0.85, kf=95, ksweep=50, krate=36, kdecay=16, kclick=0.5, kcd=220, stone=0.42, sf=180, sdecay=14, snoise=1.0, snd=20, hdecay=75, odecay=11, hp=200, eq_f=2400, eq_w=0.9, eq_g=5, clip=0.72, bits=12, cmix=0.4, lpc=8500, kgates=1\|0\|0\|0\|0\|0\|1\|0\|0\|0\|0\|0\|0\|0\|1\|0\|1\|0\|0\|0\|0\|0\|1\|0\|0\|0\|1\|0\|0\|0\|0\|0, kvel=1\|1\|1\|1\|1\|1\|0.9\|1\|1\|1\|1\|1\|1\|1\|0.75\|1\|1\|1\|1\|1\|1\|1\|0.9\|1\|1\|1\|0.8\|1\|1\|1\|1\|1, sgates=0\|0\|0\|0\|1\|0\|0\|1\|0\|0\|0\|0\|1\|0\|0\|0\|0\|0\|0\|0\|1\|0\|0\|1\|0\|0\|0\|0\|1\|0\|0\|1, svel=1\|1\|1\|1\|1\|1\|1\|0.32\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|0.28\|1\|1\|1\|1\|1\|1\|1\|0.34, hgates=1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|0\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0, hvel=0.85\|1\|0.45\|1\|0.7\|1\|0.4\|1\|0.9\|1\|0.5\|1\|0.75\|1\|1\|1\|0.85\|1\|0.45\|1\|0.7\|1\|0.4\|1\|0.9\|1\|0.5\|1\|0.8\|1\|0.45\|1, ogates=0\|0\|0\|0\|0\|0\|0\|1\|0\|0\|0\|0\|0\|0\|0\|0\|0\|0\|0\|0\|0\|0\|0\|1\|0\|0\|0\|0\|0\|0\|0\|0, ovel=1\|1\|1\|1\|1\|1\|1\|0.7\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|1\|0.65\|1\|1\|1\|1\|1\|1\|1\|1 |
| roll    | roll.txt      | amp=0.95, decay=16, vmin=0.35, vspan=0.65, tone=0.4, sf=200, snoise=0.95, nd=18, hp=180, clip=0.75, lpc=7000 |
| sub     | sub.txt       | amp=0.4, atk=6, dec=0.7, harm=0.12, lp_bass=120, lp_q=0.7, eq_f=48, eq_g=3.5, sub_cut=80, sub_boost=5, sub_dry=0.7, sub_wet=0.8, clip=0.85, note_def=36.71, notes=36.71\|49\|58.27\|55 |
| ep      | ep.txt        | amp=0.13, atk=2.2, sus=0.66, dec=0.7, rel=5, fm_amt=0.7, mdec=10, ratio=2, v2=0.65, v3=0.42, hp=180, eq_f=500, eq_g=1.5, clip=0.6, bits=13, cmix=0.15, lpc=3800, note_def=220, gates=1\|1\|1\|1\|1\|1\|1\|1, n1=220\|220\|233.08\|233.08\|293.66\|293.66\|277.18\|277.18, n2=261.63\|261.63\|293.66\|293.66\|349.23\|349.23\|329.63\|329.63, n3=329.63\|329.63\|349.23\|349.23\|440\|440\|392\|392 |
| strings | strings.txt   | amp=0.08, base=0.8, amt=0.2, period=14, atk=0.8, det=0.65, detune=1.005, v2=0.55, v3=0.4, hp=100, lpc=1400, note_def=110, n1=110\|116.54\|146.83\|138.59, n2=130.81\|146.83\|174.61\|164.81, n3=164.81\|174.61\|220\|196 |
| bell    | bell.txt      | amp=0.48, dec=2.4, idx=1.05, mdec=8, ratio=2.2, hp=350, clip=0.65, lpc=5200, echo=1071, edec=0.22, note_def=293.66, gates=1\|0\|1\|0\|1\|0\|0\|1\|0\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|1\|0\|0\|1\|0\|1\|1\|1\|0\|0, notes=293.66\|293.66\|440\|440\|349.23\|349.23\|349.23\|523.25\|523.25\|523.25\|440\|440\|392\|392\|349.23\|349.23\|293.66\|293.66\|440\|440\|349.23\|349.23\|329.63\|329.63\|329.63\|523.25\|523.25\|440\|392\|349.23\|349.23\|349.23 |
| stab    | dubstab.txt   | amp=0.32, decay=14, v2=0.7, v3=0.45, hp=250, lpc=4800, clip=0.6, note_def=440, gates=0\|0\|0\|0\|0\|0\|0\|0\|0\|0\|0\|0\|0\|0\|0\|0\|0\|0\|0\|0\|0\|0\|0\|0\|0\|0\|0\|0\|0\|0\|1\|0, n1=440\|466.16\|523.25\|415.3, n2=523.25\|587.33\|659.25\|493.88, n3=659.25\|698.46\|880\|587.33, dry_l=0.4, dry_r=0.6, ltaps=1071\|2143\|3214, ldec=0.5\|0.28\|0.12, rtaps=714\|1786\|2857, rdec=0.42\|0.22\|0.1 |
| horn    | horn.txt      | amp=0.16, atk=1.4, sus=0.75, dec=0.28, vib_amt=0.004, vib_f=4.2, det=0.25, detune=1.003, breath=0.12, breath_dec=1.2, hp=200, f1=700, q1=1.4, g1=4, f2=1400, q2=1.1, g2=2.5, clip=0.7, lpc=2800, note_def=196, gates=0\|1\|0\|1, notes=196\|196\|220\|220 |
| rise    | rise.txt      | amp=0.28, start=0.84, tone=0.22, f0=140, oct=0.7, hp=300, lpc=2400 |
| vinyl   | vinyl.txt     | amp=0.22, hiss=0.65, pop=0.85, th=0.9999972, wow=0.9, wow_amt=0.1, wow_f=0.35, hp=1800, lpc=8000, eq_f=3200, eq_g=3 |
