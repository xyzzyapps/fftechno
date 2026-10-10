# SPEC.md - ffmpeg_techno (SRS)

Specification of the **ffmpeg_techno** deliverable: a **hardgroove techno beat**
with a **granular robotic-speech** voice, synthesized entirely by ffmpeg, plus a
**VapourSynth countdown visualizer** combined into a final video. This document is
the authoritative spec for the current build and for any future agent extending it.

---

## 1. Purpose and scope

Produce a fixed-length musical loop ("hardgroove beat") that includes a distinct
**granular robotic-speech** layer, using only `ffmpeg` command line, and render a
**film-leader countdown** visual with VapourSynth that is muxed with the track into
an MP4. No DAW, no sample libraries, no Python for the audio.

In scope:
- Oscillator/noise synthesis, per-instrument expression sequencing (ffmpeg eval).
- Hardgroove kit: punchy kick, offbeat open hats, syncopated toms, rolling bass.
- Granular synthesis + speech-like per-grain pitch contour for the voice.
- VapourSynth visualizer (numpy drawing) + ffmpeg encode/mux.
- Reproducible build + verification.

Out of scope (non-goals):
- Real-time performance / GUI.
- General-purpose sequencer or MIDI import.
- Sample playback.
- Any Python for the *audio* synthesis (VapourSynth is Python by nature and is
  used only for the video).

## 2. Glossary

- **Expression**: ffmpeg `eval` string evaluated per sample by `aevalsrc`.
  Available: `t`, `n`, `s`, `PI`, `sin`, `cos`, `exp`, `mod`, `floor`, `lt`, `gt`,
  `eq`, `if`, `random(x)`.
- **Stem**: a single-instrument mono WAV rendered to `output/stems/`.
- **Grain**: one short windowed burst of a carrier.
- **Slot**: one 16th-note cell; the voice reads a per-slot pitch/gate contour.

## 3. Global constants

| Name        | Value (s)  | Derivation                          |
|-------------|-----------|-------------------------------------|
| BPM         | 140        | hardgroove tempo                    |
| sample rate | 48000 Hz   | `aevalsrc` `s=`                     |
| beat        | 0.428571   | `60/140`                            |
| eighth      | 0.214286   | `beat/2`                            |
| sixteenth   | 0.107143   | `beat/4`                            |
| bar         | 1.714286   | `beat*4`                            |
| half-bar    | 0.857143   | voice phrase period                 |
| bars        | 8          | fixed                               |
| duration    | 13.714     | `bar*8` (via `aevalsrc` `d=`)       |
| master dur. | 13.769     | loudnorm adds ~55 ms of padding     |
| channels    | 2 (stereo) | mono stems -> stereo at mix         |
| codec       | pcm_s16le  | final; stems are pcm_f32le          |

## 4. Architecture and data flow

```
                       filters/<stem>.txt  (aevalsrc expression -> [out])
  kick  clap  hat  ohat  perc  bass  growl
    |     |     |     |     |     |     |
    v     v     v     v     v     v     v
  (ffmpeg -filter_complex_script per file, one pass each)
    |     |     |     |     |     |     |
    v     v     v     v     v     v     v
  output/stems/*.wav   (mono, f32, 48k, 13.714s)  -- 7 stems
                       |
                       v
   filters/mix.txt  (7 inputs -> duck -> sum -> bus compressor)  -- pass A
                       |
                       v
                output/mix_pre.wav   (stereo, f32, 48k)
                       |
                       v
   filters/master.txt (2-pass linear loudnorm -> limiter -> s16 stereo)  -- pass B
                       |
                       v
                output/techno.wav    (stereo, s16, 48k)

   visualizer.vpy (VapourSynth, numpy) --vspipe -c y4m--> ffmpeg (+ techno.wav)
                       |
                       v
                output/techno_visualizer.mp4
```

Layers:
- **Instrument layer** - one filter script per sound (7) + mix + master.
- **Shared conventions** - source first, effects chained with `,`, chains
  separated with `;`, final label `[out]`, expressions quoted with `'...'`.
- **No state** - each pass is a stateless ffmpeg invocation; only the
  intermediate WAVs persist.

## 5. Build pipeline (phases)

1. **Stem pass** (x7): `ffmpeg -filter_complex_script filters/<s>.txt -map "[out]"
   -c:a pcm_f32le output/stems/<s>.wav`.
2. **Mix pass**: `-i` seven stems, `-filter_complex_script filters/mix.txt`,
   output `pcm_f32le output/mix_pre.wav`.
3. **Master pass**: `-i output/mix_pre.wav`, `-filter_complex_script
   filters/master.txt`, output `pcm_s16le output/techno.wav`.
4. **Video pass**: `vspipe -c y4m visualizer.vpy - | ffmpeg ... output/techno_visualizer.mp4`.

`build.ps1` runs phases 1-3; `build_video.ps1` runs phase 4.

## 6. Instrument specifications

Notation: `T=0.428571`, `T8=0.214286`, `T16=0.107143`, `B=1.714286`.

### 6.1 Kick - `filters/kick.txt`

Punchy 909-style 4-on-the-floor. Instantaneous frequency sweeps ~268 Hz -> 48 Hz
fast (phase uses the sweep integral); a very short 1200 Hz click adds attack.

```
tau = mod(t, T)
0.95 * ( sin(2*PI*( 48*tau + (220/55)*(1-exp(-55*tau)) )) * exp(-24*tau)
       + 0.4 * sin(2*PI*1200*tau) * exp(-420*tau) )
filter: equalizer=f=60:t=q:w=1:g=3
```

### 6.2 Clap - `filters/clap.txt`

Noise burst + short 200 Hz tone on beats 2 and 4.

```
gate = gt( mod( floor(mod(t,B)/T), 2 ), 0.5 )
0.55 * ( ((random(0)*2-1)*exp(-20*tau)) + 0.5*sin(2*PI*200*tau)*exp(-28*tau) ) * gate
filters: highpass=f=900, lowpass=f=9000
```

### 6.3 Closed hat - `filters/hat.txt`

```
0.35 * (random(0)*2-1) * exp(-95*mod(t, T16))
filter: highpass=f=7000
```

### 6.4 Offbeat open hat - `filters/ohat.txt`

The hardgroove "&" hat. `tau_o = mod(t + T8, T)` (positive offset avoids `mod`
sign surprises) resets on the offbeat; a gate limits it to the first 200 ms.

```
0.4 * (random(0)*2-1) * exp(-15*tau_o) * if(lt(tau_o, 0.20), 1, 0)
filter: highpass=f=6500
```

### 6.5 Toms/congas - `filters/perc.txt`

Syncopated pitched toms for the tribal hardgroove roll. Step index
`K = floor(mod(t,B)/T16)`. Hits at steps {1,3,6,9,11,14}; pitch map:
1->196, 3->147, 6->175, 9->131, 11->165, 14->147 Hz. Each hit is a sine with a
fast downward pitch drop.

```
delta = mod(t, T16)
0.7 * ( sin(2*PI*( P*delta + (P*1.1/28)*(1-exp(-28*delta)) )) * exp(-16*delta) * G(K) )
filters: highpass=f=110, lowpass=f=3500, aecho=0.8:0.7:55:0.25
```

### 6.6 Bass - `filters/bass.txt`

Rolling saw bass, one note per 16th. `K = floor(mod(t,B)/T16)`.

| K      | Hz  |
|--------|-----|
| 0-5    | 55  |
| 6      | 110 |
| 7      | 55  |
| 8-13   | 49  |
| 14     | 98  |
| 15     | 49  |

```
0.6 * (mod(F*mod(t,T16), 1)*2 - 1) * exp(-14*mod(t,T16))
filters: lowpass=f=1500, equalizer=f=90:t=q:w=1:g=4
```

### 6.7 Granular robotic-speech voice - `filters/growl.txt` (centrepiece)

Designed to read as **robotic speech**, built from three stacked ideas.

**(a) Syllable window.** `slot = mod(t, T16)`. The voice is gated to the first
70 ms of each 16th slot by a Hann window, so grains are separated -> syllables:

```
W = if(lt(slot,0.070), sin(PI*slot/0.070)^2, 0)
```

**(b) Grain train (granular).** Four overlapping Hann grains per 63 ms period
(46 ms grains), summed, so each syllable is a grain cloud:

```
G2 = sum_{k=0..3} w2( mod(t + (0.063 - k*0.016), 0.063) / 0.046 )
w2(x) = if(lt(x,1), sin(PI*x)^2, 0)
```

**(c) Formant-rich FM carrier with a per-grain pitch contour.** Over an 8-slot
half-bar phrase, `K = floor(mod(t,0.857143)/T16)`, pitch `P(K)` and gate `G(K)`:

| K   | 0    | 1    | 2    | 3 (rest) | 4    | 5    | 6    | 7 (rest) |
|-----|------|------|------|----------|------|------|------|----------|
| P   | 1.00 | 1.19 | 1.08 | -        | 0.84 | 0.75 | 1.12 | -        |
| G   | 1    | 1    | 1    | 0        | 1    | 1    | 1    | 0        |

The varying pitch is the per-grain pitch variation that gives speech intonation.

```
carrier = 0.6*(mod(65*P*slot + 1.5*sin(2*PI*12*t), 1)*2 - 1)   # FM saw
        + 0.4*sin(2*PI*65*P*slot)                               # 2nd harmonic
R = 0.6 + 0.4*sin(2*PI*173*t)                                   # robotic ring mod
voice = 0.85 * W * G2 * carrier * R * G
filters: equalizer=f=380:t=q:w=3:g=8, equalizer=f=1100:t=q:w=3:g=7,
         equalizer=f=2600:t=q:w=3:g=6,          # vowel formants
         acrusher=bits=7:mix=0.5:mode=log,     # grit
         asoftclip=type=tanh:threshold=0.7,    # saturation
         lowpass=f=7000
```

### 6.8 Instrument design rules

- Never let a stem exceed 0 dBFS: fix at the source, not at the mix bus.
- Prefer short, decaying envelopes so `mod` gating needs no explicit `[0,1]` gate.
- Keep expressions free of `NaN` risk: divisors are non-zero constants.
- Quote every expression with single quotes; keep parentheses balanced (the
  `perc` tom sweep is the easiest place to miscount).

## 7. Mix specification - `filters/mix.txt`

Inputs (order matters): `0=kick 1=clap 2=hat 3=ohat 4=perc 5=bass 6=growl`.

```
[5]volume=0.9[bass];
[6]volume=1.25[growl];
[bass][growl]amix=inputs=2:normalize=0[low];
[0]asplit=2[kick][key];
[low][key]sidechaincompress=threshold=0.05:ratio=8:attack=5:release=120:makeup=1[lowd];
[1]volume=0.7[clap];
[2]volume=0.55[hat];
[3]volume=0.5[ohat];
[4]volume=0.7[perc];
[lowd][clap][hat][ohat][perc][kick]amix=inputs=6:normalize=0[sum];
[sum]aformat=channel_layouts=stereo,acompressor=threshold=0.1:ratio=3:attack=10:release=150[out]
```

- **Sidechain duck**: kick duck the bass+voice bus so the low end pumps.
- `amix=normalize=0` preserves levels. `aformat=channel_layouts=stereo` up-mixes
  the mono sum. Bus compressor glues the six-way sum. No limiting here.

## 8. Master specification - `filters/master.txt`

Two-pass linear loudness normalisation (measure on `mix_pre.wav`, then apply) plus
a true-peak limiter.

```
[0]loudnorm=I=-14:TP=-1.0:LRA=11:measured_I=-20.71:measured_TP=-5.80:
   measured_LRA=0.20:measured_thresh=-30.71:offset=0.20:linear=true:
   print_format=summary,
   alimiter=limit=0.80:level=disabled,
   aresample=48000,aformat=sample_fmts=s16:channel_layouts=stereo[out]
```

The `measured_*` values are those loudnorm reported for *this* deterministic mix.
Re-measure after any tempo/pattern change:

```powershell
ffmpeg -i output/mix_pre.wav -af loudnorm=I=-14:TP=-1:LRA=11:print_format=json -f null -
```

Note: `alimiter` **must** set `level=disabled`; its default auto-level would boost
back over the ceiling. In linear mode loudnorm alone does not guarantee true peak,
so the limiter enforces the ceiling.

## 9. Output format

`output/techno.wav`: PCM signed 16-bit LE, 48 000 Hz, 2 channels, ~13.77 s.

## 10. Verification and acceptance criteria

| Check | Command | Result |
|-------|---------|--------|
| Graph validity | `ffmpeg -v error -filter_complex_script filters/*.txt -map "[out]" -f null -` | clean (no stderr) |
| Integrated loudness | `ebur128` | **-14.4 LUFS** |
| True peak | `ebur128=peak=true` | **-1.5 dBFS** (target < -1.0 met) |
| Duration/channels | `ffprobe` | ~13.77 s, 48000 Hz, 2 ch |
| Determinism | render twice, compare `-f framecrc` | identical |
| Voice structure | `showwavespic` of `growl.wav` | discrete syllable bursts with rests |
| Groove | `showspectrumpic` of `techno.wav` | 16th stripes + offbeat + tom accents |

Acceptance criteria for any future edit: all rows hold, and the voice retains
(a) overlapping grains, (b) per-grain pitch contour, (c) ring modulation,
(d) formant EQ + bit-crush.

## 11. Determinism

`random(x)` in `hat`/`ohat`/`clap` is seeded and evaluated deterministically for a
fixed sample count, so the render is byte-reproducible.

## 12. Extension guide

- **Change tempo**: update `T/T8/T16/B` inline literals everywhere, the `d=`
  durations, and `BAR` in `visualizer.vpy`; then re-measure loudnorm.
- **Add an instrument**: create `filters/<name>.txt` ending in `[out]`, add it to
  the stem list in `build.ps1`, add an `-i output/stems/<name>.wav` to the mix
  command, and wire a new label in `filters/mix.txt`.
- **Swing/shuffle** (future): offset the odd-16th gate phase in `hat`/`perc`.

## 13. Risks / limitations

- No user variables in ffmpeg `eval` -> verbose expressions with repeated constants.
- `loudnorm` runs internally at 192 kHz; the following `aresample=48000` is required.
- The loop's measured LRA is tiny (uniform club loop); this is inherent to the
  material, not a mastering artifact.
- `random()` noise timbre depends on ffmpeg's eval seeding; a different ffmpeg
  build may shift it.

## 14. File inventory

```
filters/kick.txt     punchy 4-on-floor kick
filters/clap.txt     clap on 2 & 4
filters/hat.txt      closed 16th hats
filters/ohat.txt     offbeat open hat
filters/perc.txt     syncopated toms/congas
filters/bass.txt     rolling saw bass
filters/growl.txt    granular robotic-speech voice
filters/mix.txt      mix graph (7 stems)
filters/master.txt   master graph (2-pass loudnorm + limiter)
build.ps1            orchestrates audio phases 1-3
visualizer.vpy       VapourSynth countdown visualizer
build_video.ps1      vspipe -> ffmpeg mux/encode -> MP4
README.md            quickstart
SPEC.md              this document
TODO.md              task log
output/techno.wav                   audio deliverable
output/techno_visualizer.mp4        video deliverable (1080p)
output/techno_visualizer_720p.mp4   web preview
output/stems/*.wav   intermediate stems
output/mix_pre.wav   intermediate bus
output/logs/*        proofs + build logs
```

---

## 15. Visualizer (VapourSynth) and final video

### 15.1 Purpose

Render an audio-reactive visual from `output/techno.wav` with VapourSynth and
combine it with the track into a final MP4. Aesthetic target: a **film-leader
"countdown"** ident (Academy-leader style) crossed with dark Berlin techno.

### 15.2 Environment and data flow

VapourSynth R81 (pip, `cp312-abi3` wheel) runs on the project Python 3.14. This
ffmpeg build has no VapourSynth input, so the pipeline is:

```
visualizer.vpy --vspipe -c y4m--> stdout --pipe--> ffmpeg --mux audio--> MP4
   (numpy draws RGB24)          (YUV420P8 y4m)   (libx264 + aac)
```

One-off setup: local `.venv`, `pip install vapoursynth numpy`, then
`vapoursynth config` (registers Python/lib paths for `vspipe`; writes
`%APPDATA%\vapoursynth\vapoursynth.toml`, the only artifact outside the project).

### 15.3 the .vpy script

- **Audio analysis (once).** `wave` + numpy reads the WAV; mono mixdown; STFT
  (2048 Hann, hop `sr/FPS = 1600`); 64 log-spaced band magnitudes (28 Hz - 16 kHz)
  + a low band (<120 Hz) for the kick, all dB-normalised against percentiles, then
  temporally smoothed (attack 0.55 / release 0.80).
- **Static layers (once).** Vignette, scanline mask, grain tile, radius/angle
  grids (`rr`, `phi` about the centre), scratch positions, bar geometry.
- **Per-frame drawing** (`compose(n)` -> float RGB):
  1. cold film-black background;
  2. rotating sweep: a trailing sector, a bright leading hand (`exp` on the
     angular difference), and an arc at `SWEEP_R` drawn only where `phi < theta`;
     `theta` advances one revolution per bar (`BAR = 60/140*4`);
  3. crosshair through the centre;
  4. a large 7-segment numeral counting down `8..1`, one per bar, drawn in numpy
     (no font files) with an amber glow and a subtle flicker;
  5. the 64-band spectrum as amber->red bars rising off the bottom edge;
  6. heavy film grain, per-frame flicker, occasional vertical scratches;
  7. kick strobe + vertical jitter on strong kicks;
  8. grade: scanlines, vignette, cool-steel tint.
- **Frame write bridge.** R81 planes are read-only memoryviews; writing uses
  `frame.copy()` then `get_write_ptr(plane).value` + `get_stride(plane)` via
  ctypes. Planes are planar RGB24 in **G, B, R** order.
- **Output.** `core.resize.Bicubic(..., format=vs.YUV420P8, matrix_s="470bg",
  range_s="limited")` (do NOT set `matrix_in_s` for RGB->YUV). The `ModifyFrame`
  callback must be `def draw(n, f)`.

### 15.4 Encode and mux

```
vspipe -c y4m visualizer.vpy - | ffmpeg -f yuv4mpegpipe -i - -i output/techno.wav \
  -c:v libx264 -preset slow -crf 20 -tune film -pix_fmt yuv420p \
  -c:a aac -b:a 192k -shortest -movflags +faststart output/techno_visualizer.mp4
```

`build_video.ps1` runs the above, then makes a 720p preview (`scale=1280:720`,
CRF 22).

### 15.5 Parameters and acceptance

| Parameter | Value |
|-----------|-------|
| Resolution / FPS | 1920x1080 / 30 |
| Frames | 414 (video 13.767 s; audio 13.769 s, `-shortest`) |
| Video codec | H.264 (libx264), CRF 20, `-tune film`, yuv420p |
| Audio codec | AAC 192 kbps |
| Deliverables | `techno_visualizer.mp4` (~46 MB), `techno_visualizer_720p.mp4` (~10 MB) |

Acceptance: `vspipe -i visualizer.vpy -` reports 1920x1080 / 30 fps / YUV420P8 /
414 frames; `ffprobe` reports one H.264 1080p30 stream and one AAC stream of equal
~13.77 s duration; sampled frames show the numeral decrementing once per bar and
the bars tracking the spectrum. Drawing runs ~2.7 fps, so a full render takes a
few minutes.

### 15.6 Visualizer risks / limitations

- This ffmpeg cannot read `.vpy` directly; `vspipe` must pipe y4m.
- `vspipe` requires the one-off `vapoursynth config` step after `pip install`.
- Numerals are 7-segment shapes drawn in numpy; a real font would need an external
  font file (outside the project) - deliberately avoided.
- The visual is deterministic: a pure function of the WAV and the frame index.
