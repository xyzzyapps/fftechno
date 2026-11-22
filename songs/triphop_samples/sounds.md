# fftechno - sampler + synth definitions

Minimal instrumental trip hop, **84 BPM**, DJ Shadow / DJ Krush mould. Four
elements only:

- `brk` - the **Amen break** (real sample), varispeeded to the 84 BPM grid
  (`rate=0.56176`) and trimmed to a two-bar loop (`trim=5.714286`). The source file's
  pattern is really ~149.5 BPM (it repeats every 1.605 s), not the "136" in its name.
  It is the only drum source (no second kit), high-passed at 200 Hz, low-passed at
  8 kHz and softly clipped so it occupies the midrange.
- `sub` - a deep **sub bass**, one bar-long note per step of a 5-bar phrase that
  drifts against the 8-bar harmony. It enters with the piano at bar 16, is laid back
  0.13 s, and is quiet and punchy.
- `ep` - a **dusty FM electric piano** on the 8-bar loop Am - Bb - Dm - A7, one
  soft attack per bar.
- `vinyl` - the dust: a **90 s record-groove sample from YouTube** (see
  `samples/manifest.md`; not CC-licensed, used noncommercially), looped every 31
  bars as-is with only a -1.9 dB gain trim (`gain=0.8`).

`pat` is a list of 16th-step indices inside the pattern (not a 16-value gate string);
`hits` places sparse hits at absolute 16th steps. `trim` is the seconds per copy;
`rate` is varispeed; `fx` is a per-hit filter chain (`;` becomes `,`).

sr: 192000
lp: 16000
osr: 48000
cstep: {{bar}}*2
cgrid: floor(mod(t,{{bar}}*8)/{{cstep}})
barstep: {{bar}}
bargrid: floor(mod(t,{{bar}}*8)/{{bar}})
unit: {{bar}}
sph: mod(t+{{bar}}-0.13,{{bar}})
sgrid: floor(mod(t+{{bar}}*5-0.13,{{bar}}*5)/{{bar}})

## Samplers

| name  | sample                  | params |
|-------|-------------------------|--------|
| brk   | samples/breaks/amen.wav | hits=0\|32\|64\|96\|128\|160\|192\|224\|256\|288\|320\|352\|384\|416\|448\|480\|512\|544\|576\|608\|640\|672\|704\|736\|768\|800\|832\|864\|896\|928\|960\|992\|1024\|1056\|1088\|1120\|1152\|1184\|1216\|1248, rate=0.56176, trim=5.714286, gain=0.8, fx=highpass=f=200;lowpass=f=8000;asoftclip=type=tanh:threshold=0.8 |
| vinyl | samples/vinyl/crackle.wav | pat=0, pat_bars=31, trim=88.571429, gain=0.8 |

## Instruments

| name  | template  | parameters |
|-------|-----------|------------|
| sub   | sub_async.txt | amp=0.26, atk=60, sus=0.35, dec=1.2, rel=10, drop=0.25, rate=70, h2=0.55, h3=0.20, pdec=16, lp_bass=110, lp_q=0.7, clip=0.95, note_def=55, gates=1\|1\|1\|1\|1, notes=55\|73.42\|65.41\|82.41\|55 |
| ep    | ep.txt    | amp=0.13, atk=2.2, sus=0.66, dec=0.7, rel=5, fm_amt=0.7, mdec=10, ratio=2, v2=0.65, v3=0.42, hp=180, eq_f=500, eq_g=1.5, clip=0.6, bits=13, cmix=0.15, lpc=3800, note_def=220, gates=1\|1\|1\|1\|1\|1\|1\|1, n1=220\|220\|233.08\|233.08\|293.66\|293.66\|277.18\|277.18, n2=261.63\|261.63\|293.66\|293.66\|349.23\|349.23\|329.63\|329.63, n3=329.63\|329.63\|349.23\|349.23\|440\|440\|392\|392 |