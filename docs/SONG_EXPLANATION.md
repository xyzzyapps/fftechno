# How `triphop_samples` is generated

Render the full song from the repo root:

```powershell
python -m fftechno samples
python -m fftechno audio --song triphop_samples
```

`samples` downloads and normalises the Amen break and the vinyl groove once.
`audio` writes the next available master (`output/triphop_samples/techno_vN.wav`;
the full render is 228.571 s). The delivered YouTube cut is `techno_v29.wav`, which
removes the first two bars (5.714286 s) for 222.857 s.

Related files: [song.md](../songs/triphop_samples/song.md),
[sounds.md](../songs/triphop_samples/sounds.md),
[manifest](../samples/manifest.md), [SPEC](../SPEC.md).

## 0. What is generated

`triphop_samples` has four stems:

| Stem | Source |
|---|---|
| `brk` | the real Amen break sample |
| `sub` | an `aevalsrc` synth sub |
| `ep` | an `aevalsrc` FM electric piano |
| `vinyl` | a YouTube record-groove sample |

Only `brk` is drums. There is no synthesized kick, snare or hat layer.

The full render is **80 bars at 84 BPM = 228.571 s**. The delivered cut removes the
first two bars, giving **222.857 s**.

## 1. Fetch the samples

`python -m fftechno samples` reads `samples/manifest.md` and downloads anything
missing:

- `samples/breaks/amen.wav` - MIT-licensed Amen copy.
- `samples/vinyl/crackle.wav` - 90 s from the YouTube vinyl video at `t=120`.

Each file is normalised to 48 kHz PCM. YouTube rows use the manifest `seconds`
column.

## 2. Parse the song and clock

`python -m fftechno audio --song triphop_samples` loads:

- `songs/triphop_samples/song.md` - arrangement, levels, pan, effects.
- `songs/triphop_samples/sounds.md` - sampler rows and instrument recipes.

From 84 BPM and 80 bars, `synth.py` computes:

- beat = `60 / 84` = **0.714286 s**
- bar = `4 x beat` = **2.857143 s**
- 16th step = `bar / 16` = **0.178571 s**
- duration = `80 x bar` = **228.571 s**

These are injected as `{{bar}}`, `{{step}}`, `{{beat}}` and `{{dur}}`.

## 3. Generate four filter graphs

`synth.generate()` writes:

```
filters/triphop_samples/brk.txt
filters/triphop_samples/sub.txt
filters/triphop_samples/ep.txt
filters/triphop_samples/vinyl.txt
```

The two sampler rows become `amovie` graphs. The two instrument rows are templates
in `templates/` with values substituted. Templates are written multiline; blank
lines and full-line `#` comments are ignored, and the remaining lines are joined
before substitution. These graph files are **generated and gitignored**;
`templates/`, `sounds.md` and the code are the source of truth.

## 4. The break: `brk.txt`

This is the actual beat.

The Amen is read with:

```text
amovie=samples/breaks/amen.wav
```

Then split into **40 copies**, one for every hit:

```text
[s0]asplit=40[s0_0]...[s0_39]
```

The hits are at absolute 16th steps:

```text
0, 32, 64, 96, ... 1248
```

That is one hit every **32 steps**, or every **two bars**:

```text
32 x 0.178571 = 5.714286 s
```

Each copy goes through:

```text
aresample=48000
aformat=mono
asetrate=26964
aresample=48000
atrim=0:5.714286
asetpts=N/SR/TB
highpass=f=200
lowpass=f=8000
asoftclip=type=tanh:threshold=0.8
volume=0.8
adelay=<absolute ms>:all=1
```

Key points:

- `asetrate=26964` is `48000 x 0.56176`. The source Amen pattern is really about
  **149.5 BPM**, not the "136" in its filename. Slowing it to `0.56176` maps it onto
  the 84 BPM grid.
- `trim=5.714286` keeps exactly **two bars per copy**.
- `adelay` places each copy at an absolute time, so there is no cumulative drift.
- The high-pass/low-pass/tanh shape the break so it sits in the midrange.
- The gain is `0.8`; no `vel` list is supplied, so every hit is velocity `1.0`.

Finally the 40 hits are summed with a silent bed of the full song length:

```text
aevalsrc='0':s=48000:d=228.571
[h0]...[h39][bed]amix=inputs=41:normalize=0:duration=longest,
asoftclip=type=tanh:threshold=0.9
```

The sampler folds the break to mono. That is why the Amen is the only drum source
and why its timing is exact: every hit is explicitly placed.

## 5. The sub: `sub.txt`

`templates/sub_async.txt` builds a single `aevalsrc` expression.

The phrase is five notes, one per bar:

```text
55 | 73.42 | 65.41 | 82.41 | 55   Hz
```

The grid is:

```text
sgrid = floor(mod(t + bar*5 - 0.13, bar*5) / bar)
```

So it is a **5-bar phrase** that drifts against the 8-bar piano harmony, delayed by
**0.13 s**.

Each note has:

- a fast attack (`atk=60`),
- sustain `0.35`,
- decay `1.2`,
- release at the bar boundary,
- a small pitch thump (`drop=0.25`, `rate=70`),
- second and third harmonics (`h2=0.55`, `h3=0.20`) that decay quickly,
- a low-pass at `110 Hz`, then the template's `16 kHz` safety filter,
- `amp=0.26`, `boost=0.9`.

The sub graph plays for the whole song, but the mix mutes it until bar 16 via the
`Sections` automation. That is why it enters with the piano.

## 6. The electric piano: `ep.txt`

`templates/ep.txt` is also one `aevalsrc` expression, using an 8-bar chord grid:

```text
bargrid = floor(mod(t, bar*8) / bar)
```

The note lists repeat each chord twice, so the 8-bar loop is:

```text
bars 0-1:  Am
bars 2-3:  Bb
bars 4-5:  Dm
bars 6-7:  A7
```

There is one attack per bar, with an FM modulator per note:

```text
sin(2*PI*f*t + fm_amt * exp(-mdec * bar_phase) * sin(2*PI*f * ratio * t))
```

Then second and third voices are mixed in at `v2=0.65` and `v3=0.42`. The chain adds:

- high-pass at 180 Hz,
- a 500 Hz EQ lift,
- tanh clip at 0.6,
- 13-bit crush at 15% mix,
- low-pass at 3.8 kHz, then 16 kHz,
- resample to 48 kHz.

## 7. The vinyl: `vinyl.txt`

This is a sampler row too:

```text
pat=0, pat_bars=31, trim=88.571429, gain=0.8
```

`pat=0` means one hit at step 0. `pat_bars=31` makes that pattern **31 bars**:

```text
31 x 2.857143 = 88.571429 s
```

The graph:

1. reads `samples/vinyl/crackle.wav`,
2. resamples and folds to mono,
3. trims to `88.571429 s`,
4. adds a silent pad to the exact loop length,
5. loops with `aloop` to the full song length,
6. trims to `228.571 s`.

There is no EQ or compression, only the gain trim and the sampler's shared
`tanh 0.9` safety clip.

## 8. Render the stems

`audio.render_stems()` runs ffmpeg once per graph:

```text
ffmpeg -/filter_complex filters/triphop_samples/brk.txt -map [out]
       -t 228.571 -c:a pcm_f32le output/triphop_samples/stems/brk.wav
```

and the same for `sub`, `ep` and `vinyl`. ffmpeg runs from the repo root so the
relative `samples/...` paths resolve.

## 9. Mix

`arrangement.build_graph()` writes `output/triphop_samples/logs/mix.txt` and runs it
with the four stems plus the reverb IR.

The arrangement is:

- **0-16:** break + vinyl only.
- **16-32:** piano and sub enter.
- **32-39:** breakdown; gains drop.
- **39-40:** one-bar stop; only vinyl.
- **40-56:** drop and main groove.
- **56-64:** space; break drops to 0.4.
- **64-72:** final push.
- **72-80:** eight-bar fade.

Per-stem boosts are:

```text
brk 1.30 | sub 0.90 | ep 1.30 | vinyl 0.85
```

The mix graph also adds:

- section automation as nested `if(lt(t,...))` expressions,
- panning,
- a reverb send at 0.2 through a 300 Hz high-pass and the convolution IR,
- `extrastereo` width 1.1,
- a bus compressor.

The sidechain key is `brk` and the low bus is `sub`, but the sidechain ratio is `1`,
so the compressor is effectively transparent - the sub is **not** ducked.

## 10. Master

The mix is written to `mix_pre.wav`, then mastered in two `loudnorm` passes:

1. measure the mix,
2. apply linear loudness normalisation to **-13 LUFS**,
3. limiter at `0.88`,
4. 9 kHz high-shelf +1.5 dB,
5. resample to 48 kHz, 16-bit with triangular dither,
6. write stereo `techno.wav` (versioned as `techno_vN.wav`).

The full render is `techno_v28.wav` (228.571 s). The delivered cut removes the first
two bars:

```text
5.714286 s
```

giving `techno_v29.wav` at **222.857 s** and the matching
`ASYNCHRONOUS_1080p.mp4`.

## 11. Complete per-stem effect list

The chain order for `sub` and `ep` lives in their templates; every value is in
`sounds.md`. The sampler's shared mono fold and `tanh 0.9` are fixed in
`sampler.py`.

### `brk`

- Per hit: `aresample=48000`, `aformat=mono`, `asetrate=26964` (rate `0.56176`),
  `atrim=0:5.714286`, `asetpts=N/SR/TB`, `highpass=200`, `lowpass=8000`,
  `asoftclip=tanh:0.8`, `volume=0.8`, absolute `adelay`.
- Sampler sum: `amix=inputs=41:normalize=0:duration=longest`,
  `asoftclip=tanh:0.9`.
- Mix: boost `1.30`, section automation, `pan` stereo `0.50/0.50`, sidechain key.

### `sub`

- Synth: `aevalsrc` with attack `60`, sustain `0.35`, decay `1.2`, release `10`;
  pitch thump `drop=0.25`, `rate=70`; harmonics `h2=0.55`, `h3=0.20`,
  `pdec=16`; `lowpass=110` with `Q=0.7`; `asoftclip=tanh:0.95`;
  `lowpass=16000`; `aresample=48000`.
- Mix: boost `0.90`, section automation from bar 16, centre pan, low bus
  (sidechain ratio `1`, so no audible ducking).

### `ep`

- Synth: `aevalsrc` with attack `2.2`, sustain `0.66`, decay `0.7`, release `5`;
  FM `fm_amt=0.7`, `mdec=10`, `ratio=2`; voices `v2=0.65`, `v3=0.42`;
  `highpass=180`; `equalizer 500 Hz +1.5 dB`; `asoftclip=tanh:0.6`;
  `acrusher bits=13, mix=0.15`; `lowpass=3800`; `lowpass=16000`;
  `aresample=48000`.
- Mix: boost `1.30`, section automation, `pan` stereo `0.50/0.50`.

### `vinyl`

- Sampler: `aresample=48000`, `aformat=mono`, `atrim=0:88.571429`,
  `asetpts=N/SR/TB`, `volume=0.8`, `adelay=0`;
  `amix=inputs=1:normalize=0`, `asoftclip=tanh:0.9`;
  `atrim=0:88.571429`, `apad=whole_len=4251429`,
  `aloop=loop=-1:size=4251429`, `atrim=0:228.571429`.
- No EQ or compression beyond the shared sampler clip.
- Mix: boost `0.85`, section automation, `pan` stereo `0.50/0.50`.

### Global mix and master

- Mix bus: reverb send `0.20`, reverb high-pass `300`, wet `1.0`, sidechain
  threshold `1.0`, ratio `1`, attack `12`, release `200`; stereo width `1.10`;
  bus compressor threshold `0.1`, ratio `3`, attack `10`, release `180`.
- Master: two-pass `loudnorm` to `-13 LUFS` / `-1 dBTP` / LRA `11`, limiter
  `0.88`, 9 kHz high-shelf `+1.5 dB`, 48 kHz 16-bit triangular dither.

## 12. How to approach writing a song like this

This is the songwriting view; the render details are above.

### 12.1 Separate the score from the instrument

| File | Song-writing role |
|---|---|
| `song.md` | the score and mixing desk: tempo, form, entrances, levels, pan, global mix effects |
| `sounds.md` | the instrument/patch sheet: one row per sound, its notes, sample and sound-design knobs |
| `templates/*.txt` | the fixed signal chain inside a synth instrument |
| `samples/manifest.md` | the sample library |

Read the effects in two layers:

- **`sounds.md` effects** shape one instrument or one sample hit.
- **`song.md` Effects** process the whole summed mix.

`Boosts`, `Sections` and `Pan` in `song.md` are not effects. They are balance,
arrangement and placement. Mastering is global and not part of the song file.

The signal flow, in song-writing terms:

```text
instrument/hit sound -> stem gain -> section gain -> pan
                     -> sum -> global reverb / width / glue -> master
```

The current project has global reverb only; there is no per-stem send table yet.
That is listed in `TODO.md`.

### 12.2 A practical writing order

1. **Set the frame.** `bpm`, `bars`, `fade_bars`. At 84 BPM, one bar is 2.857 s;
   80 bars is 228.571 s.
2. **Choose roles, not instruments.** Decide what each layer is for before naming
   a sound.
3. **Build the pulse.** Get the break or drum loop to fit the bar grid; shape it
   with per-hit `fx`.
4. **Write the harmony.** For `triphop_samples`, an 8-bar loop:
   `Am | Bb | Dm | A7`.
5. **Write the bass as a counterline.** Use a phrase length that does not match the
   harmony: five bars against eight.
6. **Add texture.** A long loop such as the 31-bar vinyl bed glues the track without
   restarting every phrase.
7. **Arrange with `Sections`.** Write the entrance, breakdown, stop, drop and fade
   before fine-tuning sounds.
8. **Balance and place.** Use `Boosts` and `Pan`; keep the sub centred.
9. **Add global mix effects last.** Reverb send, bus compression, width, sidechain.
10. **Tune the sound design last.** Per-hit `fx` and the `sub`/`ep` template knobs.

### 12.3 The four roles in `triphop_samples`

| Role | Sound | Writing job |
|---|---|---|
| pulse/backbone | Amen break | carries the rhythm; the only drum source |
| low melody | sub | five-bar phrase drifting against the harmony |
| harmony | electric piano | 8-bar chord loop, one attack per bar |
| texture | vinyl | 31-bar atmosphere loop at low gain |

Four strong roles are easier to arrange than twelve weak layers.

### 12.4 How the parts relate

- The **Amen** is cut to two bars. Its `rate` makes the source loop fit the 84 BPM
  grid.
- The **piano** changes chord every two bars inside an 8-bar loop.
- The **sub** holds one note per bar for five bars, so it drifts against the piano.
- The **vinyl** loops every 31 bars, so it does not line up with the 8-bar phrase.
- The **one-bar stop** at 39-40 is an arrangement decision, not an effect.
- The **sidechain ratio is 1**, so the sub is not ducked; its low level does the
  work.
- The **global reverb** is a send from the whole mix, not a per-stem insert.

That is the whole chain: **Amen sample -> 40 absolute sampler hits -> stem WAV ->
automated mix -> two-pass master -> two-bar trim**.