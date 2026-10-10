# SPEC.md - ffmpeg_techno (SRS)

Specification of the **ffmpeg_techno** deliverable: a techno beat with a granular
robotic growl, synthesized entirely by ffmpeg. This document is the authoritative
spec for the current build and for any future agent extending it.

---

## 1. Purpose and scope

Produce a fixed-length musical loop ("techno beat") that includes a distinct
**granular robotic growl** layer, using only `ffmpeg` command line. No Python, no
DAW, no sample libraries. "Synthesis" means generating audio from scratch via
ffmpeg's expression evaluator and DSP filters.

In scope:
- Oscillator/noise synthesis, per-instrument expression sequencing.
- Granular synthesis emulated from ffmpeg primitives.
- Robotic/growl timbre via FM, ring modulation, waveshaping, bit-crush and EQ.
- Stem rendering, mixing, sidechain ducking, two-pass loudness mastering.
- Reproducible build + verification.

Out of scope (non-goals):
- Real-time interactive performance / a GUI.
- General-purpose sequencer or arbitrary MIDI import.
- Any scripting language for synthesis (Python etc. is explicitly excluded).
- Sample playback.

## 2. Glossary

- **Expression**: ffmpeg `eval` string evaluated per sample by `aevalsrc`/`aeval`.
  Available: `t` (seconds), `n` (sample index), `s` (rate), `PI`, `sin`, `cos`,
  `exp`, `mod`, `floor`, `lt`, `gt`, `eq`, `if`, `random(x)`.
- **Stem**: a single-instrument mono WAV rendered to `output/stems/`.
- **Grain**: one short windowed burst of a carrier.
- **Grain train**: overlapping sequence of grains forming a cloud.

## 3. Global constants

| Name       | Value (s)  | Derivation                        |
|------------|-----------|-----------------------------------|
| BPM        | 130        | fixed                             |
| sample rate| 48000 Hz   | `aevalsrc` `s=`                   |
| beat       | 0.461538   | `60/130`                          |
| eighth     | 0.230769   | `beat/2`                          |
| sixteenth  | 0.115385   | `beat/4`                          |
| bar        | 1.846154   | `beat*4`                          |
| bars       | 8          | fixed                             |
| duration   | 14.769     | `bar*8` (set via `aevalsrc` `d=`) |
| channels   | 2 (stereo) | mono stems -> stereo at mix       |
| codec      | pcm_s16le  | final; stems are pcm_f32le        |

## 4. Architecture and data flow

```
                       filters/<stem>.txt  (aevalsrc expression -> [out])
   kick.txt  clap.txt  hat.txt  bass.txt  growl.txt
        |         |        |        |         |
        v         v        v        v         v
   (ffmpeg -filter_complex_script per file, one pass each)
        |         |        |        |         |
        v         v        v        v         v
   output/stems/{kick,clap,hat,bass,growl}.wav   (mono, f32, 48k, 14.769s)
                        |
                        v
        filters/mix.txt  (5 inputs -> duck -> sum -> bus compressor)
                        |
                        v
                 output/mix_pre.wav   (stereo, f32, 48k)   -- pass A
                        |
                        v
        filters/master.txt (2-pass linear loudnorm -> resample -> s16 stereo)
                        |
                        v
                 output/techno.wav    (stereo, s16, 48k, 14.769s)  -- pass B
```

Layers:
- **Instrument layer** - one filter script per sound (7 files total incl. mix/master).
- **Shared conventions** - all scripts: source first, effects chained with `,`,
  graph chains separated with `;`, final label `[out]`, expressions quoted with
  `'...'` so inner commas survive filtergraph parsing.
- **No state** - each pass is a stateless ffmpeg invocation; the only persisted
  state is the intermediate WAVs.

## 5. Build pipeline (phases)

1. **Stem pass** (x5): `ffmpeg -filter_complex_script filters/<s>.txt -map "[out]"
   -c:a pcm_f32le output/stems/<s>.wav`.
2. **Mix pass**: `-i` five stems, `-filter_complex_script filters/mix.txt`,
   output `pcm_f32le output/mix_pre.wav`.
3. **Master pass**: `-i output/mix_pre.wav`, `-filter_complex_script
   filters/master.txt`, output `pcm_s16le output/techno.wav`.

`build.ps1` executes these three phases in order and aborts on non-zero exit.

## 6. Instrument specifications

Notation: `T=0.461538`, `T8=0.230769`, `T16=0.115385`, `B=1.846154`.
All amplitudes are relative; final loudness is set by the master.

### 6.1 Kick - `filters/kick.txt`

4-on-the-floor. Instantaneous frequency sweeps ~280 Hz -> 50 Hz; the phase uses
the integral of the sweep for a natural drop; a short 1 kHz click adds attack.

```
0.9 * ( sin(2*PI*( 50*tau + (230/45)*(1-exp(-45*tau)) )) * exp(-22*tau)
      + 0.35 * sin(2*PI*1000*tau) * exp(-300*tau) )
   where tau = mod(t, T)
```

`exp(-22*tau)` decays within the beat, so the `mod` naturally yields one kick per
beat. Expected level: peak ~ -0.1 dBFS at the source (trimmed in the mix by the
bus stage). Rationale: the integral term `(230/45)*(1-exp(...))` keeps the phase
continuous, avoiding the clicks a naive `f(t)*t` sweep produces.

### 6.2 Clap/snare - `filters/clap.txt`

Noise burst + short 180 Hz tone on beats 2 and 4.

```
gate = gt( mod( floor(mod(t,B)/T), 2 ), 0.5 )
0.5 * ( ((random(0)*2-1)*exp(-18*tau)) + 0.5*sin(2*PI*180*tau)*exp(-25*tau) ) * gate
   where tau = mod(t, T)
filters: highpass=f=900, lowpass=f=9000
```

`floor(mod(t,B)/T)` is the beat index 0..3; `mod(...,2) > 0.5` is true on beats
1 and 3 (0-based) = musical beats 2 and 4. Level trimmed 0.5x to fix earlier
+1.3 dBFS overshoot.

### 6.3 Hi-hat - `filters/hat.txt`

```
0.4 * (random(0)*2-1) * exp(-80*mod(t, T16))
filters: highpass=f=6500
```

Short white-noise ticks on every 16th; high-pass makes them cymbal-like. Level
trimmed 0.4x (was +2.0 dBFS).

### 6.4 Bass - `filters/bass.txt`

Saw bass, one note per 16th, A-minor flavour. Step index
`K = floor(mod(t,B)/T16)` (0..15). Frequency map:

| K        | Hz  |
|----------|-----|
| 0-5      | 55  |
| 6        | 110 |
| 7        | 55  |
| 8-13     | 49  |
| 14       | 98  |
| 15       | 49  |

```
F(K) = if(lt(K,6),55, if(lt(K,8), if(lt(K,7),110,55),
        if(lt(K,14),49, if(eq(K,14),98,49))))
0.6 * (mod(F * mod(t,T16), 1)*2 - 1) * exp(-12*mod(t,T16))
filters: lowpass=f=1400, equalizer=f=80:t=q:w=1:g=4
```

Per-step phase `mod(F*sixteenth) ` restarts each note (plucky). `mod(x,1)*2-1` is
a saw. Low-pass + 80 Hz shelf tames it.

### 6.5 Granular robotic growl - `filters/growl.txt`  (centrepiece)

Three stacked ideas:

**(a) Grain train (granular).** Period `P=0.072`, hop `hop=0.018`, grain length
`dur=0.05` (so ~2.8x overlap). Four grains per period:

```
x_k  = mod(t + (P - k*hop), P) / dur     for k = 0,1,2,3
w(x) = if(lt(x,1), sin(PI*x)*sin(PI*x), 0)     # Hann-ish window, 0 outside [0,1)
G    = sum_k w(x_k)
```

Positive offsets `(P-k*hop)` avoid any sign ambiguity in `mod`. Because
`dur > hop`, adjacent windows overlap -> a grain cloud rather than discrete ticks.

**(b) Growl carrier (FM).** Two detuned FM voices:

```
C  = sin(2*PI*( 55.0*t  + 6*sin(2*PI*7.0*t) ))
C2 = sin(2*PI*( 55.5*t  + 6*sin(2*PI*7.3*t) ))
carrier = C + 0.6*C2
```

The 7 Hz modulator with index 6 produces the growling, formant-shifting timbre.

**(c) Robotic ring modulation + rhythm.**

```
R    = 0.5 + 0.5*sin(2*PI*137*t)          # 137 Hz, inharmonic -> metallic/robot
gate = 0.35 + 0.65*exp(-8*mod(t, T8))     # hits every 8th, floor sustains
Growl = 0.7 * G * carrier * R * gate
```

Effect chain:

```
equalizer=f=300:t=q:w=2:g=6,
equalizer=f=900:t=q:w=2:g=8,
equalizer=f=2400:t=q:w=2:g=5,     # formant bumps -> vocal/growl character
acrusher=bits=6:mix=0.7:mode=log,  # bit + sample-rate reduction -> grit
asoftclip=type=tanh:threshold=0.7, # saturation -> harmonics
lowpass=f=6500                     # tame hiss
```

Source level: peak -3.1 dBFS, RMS -9.9 dBFS.

### 6.6 Instrument design rules

- Never let a stem exceed 0 dBFS: fix at the source, not at the mix bus.
- Prefer short, decaying envelopes so `mod` gating needs no explicit `[0,1]` gate.
- Keep expressions free of `NaN` risk: `dur`, `hop`, `P` are non-zero constants.
- Quote every expression with single quotes.

## 7. Mix specification - `filters/mix.txt`

Inputs (order matters): `0=kick 1=clap 2=hat 3=bass 4=growl`.

```
[3]volume=0.9[bass];
[4]volume=0.8[growl];
[bass][growl]amix=inputs=2:normalize=0[low];
[0]asplit=2[kick][key];
[low][key]sidechaincompress=threshold=0.05:ratio=8:attack=5:release=120:makeup=1[lowd];
[1]volume=0.7[clap];
[2]volume=0.6[hat];
[lowd][clap][hat][kick]amix=inputs=4:normalize=0[sum];
[sum]aformat=channel_layouts=stereo,
     acompressor=threshold=0.1:ratio=3:attack=10:release=150[out]
```

- **Sidechain duck**: the kick duck the bass+growl bus (`sidechaincompress`), so
  the low end pumps with the groove.
- `amix=normalize=0` preserves levels (default normalises by input count).
- `aformat=channel_layouts=stereo` up-mixes the mono sum.
- Bus compressor glues the four-way sum. No limiting/normalising here - the
  master pass owns loudness.
- Output: `output/mix_pre.wav` (stereo, f32, 48k).

## 8. Master specification - `filters/master.txt`

Two-pass linear loudness normalisation (measure on `mix_pre.wav` first, then apply).

```
[0]loudnorm=I=-14:TP=-1.0:LRA=11:measured_I=-19.80:measured_TP=-4.93:
   measured_LRA=0.10:measured_thresh=-29.80:offset=0.01:linear=true:
   print_format=summary,
   aresample=48000,aformat=sample_fmts=s16:channel_layouts=stereo[out]
```

The `measured_*` values are the ones loudnorm reported for *this* deterministic
mix. If you change tempo/patterns, re-measure:

```powershell
ffmpeg -i output/mix_pre.wav -af loudnorm=I=-14:TP=-1:LRA=11:print_format=json -f null -
```

and paste the `input_i/input_tp/input_lra/input_thresh/target_offset` values into
`measured_I/measured_TP/measured_LRA/measured_thresh/offset` in `filters/master.txt`.

Target: **-14 LUFS integrated** (streaming), **-1 dBTP** ceiling, `linear=true` so
the loop's (already tiny) dynamics are preserved rather than pumped.

## 9. Output format

`output/techno.wav`: PCM signed 16-bit little-endian, 48 000 Hz, 2 channels,
14.769 s, ~2.84 MB.

## 10. Verification and acceptance criteria

| Check | Command | Result |
|-------|---------|--------|
| Graph validity | `ffmpeg -v error -filter_complex_script filters/*.txt -map "[out]" -f null -` | clean (no stderr) |
| All stems non-silent | `astats` per stem | peak between -6 and 0 dBFS |
| Integrated loudness | `ebur128` | **-14.0 LUFS** |
| True peak | `ebur128=peak=true` | **-1.8 dBFS** (< -1.0 target met) |
| Clipping | `astats` "Flat factor" / clips | none (flat factor 0) |
| Duration/channels | `ffprobe` | 14.769 s, 48000 Hz, 2 ch |
| Determinism | render twice, compare `-f framecrc` | **identical** |
| Granular structure | `showspectrumpic` of growl | vertical grain striations + 55 Hz harmonic series |

Acceptance criteria for any future edit: all rows above hold, and the growl retains
(a) overlapping grains, (b) FM carrier, (c) ring modulation, (d) formant EQ +
bit-crush. If any of those four is dropped the sound is no longer "granular
robotic growl".

## 11. Determinism

`random(x)` in `hat`/`clap` is seeded and evaluated deterministically by ffmpeg
for a fixed sample count, so the render is byte-reproducible. Verified by
comparing `framecrc` of two independent renders: identical. Consequence:
`output/` can be regenerated and diffed.

## 12. Extension guide

- **Change tempo**: update `T/T8/T16/B` everywhere (they are inline literals -
  ffmpeg `eval` has no user variables) and the `d=` durations, then re-measure
  loudnorm.
- **Add an instrument**: create `filters/<name>.txt` ending in `[out]`, add it to
  the stem list in `build.ps1`, add an `-i output/stems/<name>.wav` to the mix
  command, and wire a new label inside `filters/mix.txt`.
- **Musical patterns**: encode step maps as nested `if(eq(K,n),value,...)` on the
  step index `K`, avoiding per-note concatenation.
- **Stereo width** (future): pan stems in `mix.txt` with `pan=stereo|c0=...|c1=...`.

## 13. Risks / limitations

- No user variables in ffmpeg `eval` -> expressions are verbose and constants are
  duplicated. Mitigate by generating expressions only if the "no Python" rule is
  ever relaxed.
- `loudnorm` runs internally at 192 kHz; the `aresample=48000` after it is required.
- The track's measured LRA is ~0.1 LU because it is a uniform club loop; this is
  inherent to the material, not an artifact of the master.
- `random()`-based noise timbre depends on ffmpeg's eval seeding; a different
  ffmpeg build/version may shift the noise timbre (the deterministic check assumes
  a fixed build).

## 14. File inventory

```
filters/kick.txt     instrument
filters/clap.txt     instrument
filters/hat.txt      instrument
filters/bass.txt     instrument
filters/growl.txt    instrument (granular robotic growl)
filters/mix.txt      mix graph
filters/master.txt   master graph (2-pass loudnorm values)
build.ps1            orchestrates phases 1-3
README.md            quickstart
SPEC.md              this document
TODO.md              task log
output/techno.wav    deliverable
output/stems/*.wav   intermediate stems
output/mix_pre.wav   intermediate bus
output/logs/*.png    spectra/waveform proofs
```
