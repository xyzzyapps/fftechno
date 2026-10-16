# SPEC.md - fftechno (SRS)

Technical specification of **fftechno**: underground tracks synthesized by
**ffmpeg**, plus a music video when the song has one. The songs are folders
under `songs/`: `basement` (155 BPM, 155 bars, 4:00), `hardgroove` (140 BPM,
140 bars, 4:00), `minimal` (100 BPM, 75 bars, 3:00), `triphop` (84 BPM, 84 bars,
4:00, audio only) and `triphop_beat` (88 BPM, 8 bars, a scratch). A voice, when
the song has a `vox` stem, comes from a local neural TTS. The build tooling is
Python. The arrangement and every instrument parameter live in markdown.

---

## 1. Purpose and scope

Produce a fixed-length techno track and a video, driven by a song's markdown files, using
`ffmpeg` for sound. The original hardgroove port to markdown was **lossless**
(substituting the recorded parameter values reproduces the original ffmpeg filter
graphs, verified by rendering comparison).

The video looks share one pipeline. `outline` draws a white silhouette and keeps
the blue hair, cut to random stills on the beat. `edge` is an RVM-matted line
drawing. `pollock` is an abstract painting from whole-frame edges. `photo` is a
still image. A song with no `video.md` is audio only (`triphop`, `triphop_beat`).
The voice is synthesised with a local neural TTS - **Kitten TTS** (`kittenml`) by
default, **Piper**, or ffmpeg **flite** - all offline.

In scope: `aevalsrc`-based synthesis, drum/gate patterns, mix automation, side-chain,
convolution reverb, two-pass loudness mastering, **sample playback** (section 21), an
RVM / `edgedetect` / silhouette video with on-screen lyrics, and a reproducible build.

Out of scope: real-time performance, a GUI, MIDI import.

## 2. Glossary

- **Stem** - one layer of the mix (kick, bass, ...). Rendered to `output/<song>/stems/`.
- **Template** - an ffmpeg filtergraph with `{{key}}` placeholders (`templates/`).
- **Instrument** - a row in `sounds.md`: a template plus the values for it.
- **Grid / step** - a 16th note. A bar is 16 steps.
- **Gate** - a per-step on/off (0/1) value; drum `gates` lists are 16 values.
- **LUFS / true peak** - loudness / peak measures used for mastering.

## 3. Global constants

| Name | Value |
|------|-------|
| BPM | 155 |
| bars | 155 (4:00) |
| sample rate | 48000 Hz (oscillators generated at 192000 Hz, then downsampled) |
| loudness target | -13 LUFS, true peak -1.0 dBFS |
| stems | kick, snare, snarefill, clap, hat, ohat, ride, crash, breakbeat, conga, shaker, reese, acid, lead_pwm, lead_fm, pad, stab, vox |

Derived: `beat = 60/155 = 0.387097 s`, `step (16th) = 0.096774 s`,
`bar = 1.548387 s`.

## 4. Architecture and data flow

```
  songs/<song>/song.md (arrangement)     songs/<song>/sounds.md + templates/
      |  arrangement.py                            |  synth.py
      v                                            v
  mix filtergraph                              filters/<song>/<name>.txt
  (output/<song>/logs/mix.txt)                       |
      |                                              |  audio.render_stems()
      |                                              v
      |                               output/<song>/stems/<name>.wav  (+ vox.wav)
      +--------------------+-------------------------+
                           v
              mix  ->  output/<song>/mix_pre.wav
                           v
              master (2-pass loudnorm)  ->  output/<song>/techno.wav
                           v
              songs/<song>/video.md -> Look (picture) + effect chain (effects.py)
                           v
              output/<song>/girl_loop.mp4
              + girl_frames.npy  /  girl_sprites.npy + girl_pick.npy
              + logs/fx.json + logs/fx/<stem>.wav (gain-applied envelopes)
                           v
              vspipe visualizer.vpy (paint + shader) -> ffmpeg -> techno_visualizer.mp4
```

## 5. Build pipeline

Commands (`python -m fftechno ...`):

Commander: every command takes `--song <name>` (default `basement`).

| Command | Phases |
|---------|--------|
| `synth --song S` | `songs/S/sounds.md` + `templates/` -> `filters/S/<name>.txt` (oscillator templates and sampler graphs) |
| `samples [--force]` | `samples/manifest.md` -> download + normalise the files under `samples/` (no `--song`) |
| `audio --song S [--safe] [--tts kitten\|piper]` | `synth` -> IR -> vocals -> stems -> mix -> master -> `output/S/techno.wav` |
| `girl --song S [--look edge\|pollock\|outline\|photo] [--mode reset\|trail\|build]` | picture source -> look -> `output/S/girl_loop.mp4` + picture data |
| `video --song S [--look ..] [--fx a,b] [--mode ..] [--boost F] [--static]` | envelopes -> render -> mux -> 720p preview -> optional re-level |
| `all --song S [--look ..] [--fx a,b] [--mode ..] [--safe] [--tts ..] [--boost F] [--static]` | `audio`, then `girl`, then `video` |
| `boost F --song S` | re-encode the MP4 audio at gain `F` (video copied) |
| `swap --song S` | replace the MP4 audio with the current master (video **copied** - the way to apply an audio-only change) |

Filtergraphs are read from files with the ffmpeg 9 syntax `-/filter_complex FILE`
(the old `-filter_complex_script` was removed).

Outputs are written with `config.unique_path`: if the target exists, the build
writes `name_v2.ext`, `_v3`, ... so existing renders are never overwritten.

A **build lock** (`output/<song>/logs/.build.lock`, created with `O_EXCL`) prevents two
builds writing the same outputs concurrently; a second run exits with a clear
message.

## 6. Control surface A - `songs/<name>/song.md`

Scalars (all required):

```
bpm: 155
bars: 155
fade_bars: 7            # the final section fades to silence over this many bars
sidechain_key: kick     # which stem drives the ducking
low_bus: reese          # stems grouped and ducked under the key
```

The final `Sections` row should be `fade_bars` long: the fade starts at that row's
first bar and reaches silence `fade_bars` later, so a longer final row leaves the end of
the track silent (and a shorter one fades before the end).

Tables (all required unless noted):

- **Stems** - `| stem |`; the mix input order (one `-i` per row). Defines which
  stems exist.
- **Boosts** - `| stem | boost |`; a per-stem gain multiplied over the section gains.
  Required for every stem that has a Sections column. A Levels-only stem (the voice)
  has no Boosts row.
- **Sections** - `| bars | <stem> | ... |`; rows are bar ranges (`start-end`),
  columns are arranged stems, cells are gains. The last section fades.
- **Pan** - `| stem | mode | left | right |`; `mode` is `center`, `haas`,
  `stereo` (with `left`/`right` gains) or `keep` - a stem that is already stereo
  (an effect built into its own graph, e.g. the ping-pong blow) is passed through
  untouched rather than folded to a point.
- **Effects** - `| effect | value |`; `reverb_send`, `reverb_hpf`, `reverb_wet`,
  `sidechain_threshold/ratio/attack/release`, `stereo_width`,
  `bus_threshold/ratio/attack/release`.
- **Levels** - `| stem | level |`; fixed level for non-arranged stems (vox).

Rules: the first section starts at bar 0; each next range starts where the previous
one ends; the last row's end equals `bars`; every Sections column is a Stem; every
stem is in Sections or Levels; every arranged stem has a Boosts row; every stem has
a `Pan` row; `low_bus` stems must be in `Stems`. Missing entries raise.

## 7. Control surface B - `songs/<name>/sounds.md` + `templates/`

`sounds.md` holds global scalars and an **Instruments** table
`| name | template | parameters |`. `synth.py` substitutes the values into
`templates/<template>` and writes `filters/<name>.txt`. No defaults: a missing
placeholder fails loudly.

**Template language**

- `{{ key }}` - value substitution (global scalar or the instrument's parameter).
- `{{ if_steps(seq; grid; default) }}` - expand a step list into a nested
  `if(eq(GRID,0),v0, if(eq(GRID,1),v1, ... , default))`. `seq` is a value (or param
  name), `grid` is an expression, `default` is a param name or a numeric literal.
- Lists are `|`-separated; inside a markdown table cell the pipe is escaped `\|`.
- `bar`, `step`, `beat` and `dur` are not written in `sounds.md`. `synth.py`
  computes them from `song.md` (`bpm` and `bars`) and injects them. One bar is
  `240/bpm` seconds, one beat is `60/bpm`, one step is a quarter of a beat, and
  `dur` is the song length. Other scalars may reference `{{bar}}`, `{{step}}` and
  `{{beat}}`. A copy of those four names in `sounds.md` fails the build.
- Other globals are per song (declared at the top of `sounds.md`). The tracks
  here use combinations of `sr, lp, osr, gold, vbase, vamt, grid, halfgrid,
  beatgrid`, plus song-local clocks such as `bgrid` and `cgrid`. An instrument
  parameter of the same name wins over an injected clock (`beat=` on a hardgroove
  drum).

A second, optional table - **Samplers** (`| name | sample | params |`) - declares
**sample-based** instruments instead of oscillator templates: each row names a file
under `samples/` played on the 16th grid. A song may have an Instruments table, a
Samplers table, or both; see section 21.

## 8. Instruments

The shared techno set is seventeen instruments, all parameterised (values in
`sounds.md`). Template *variants* that add per-instrument effects are listed after
the table. `triphop` adds `boom.txt`, `break_sp.txt`, `roll.txt`, `sub.txt`,
`ep.txt`, `strings.txt`, `bell.txt`, `dubstab.txt`, `horn.txt`, `rise.txt` and
`vinyl.txt`. `triphop_beat` uses `break_synth.txt`, `kick_trip.txt` and
`bass_gate.txt`. `sax.txt` and `rhodes.txt` are examples. They are not in the
shipped trip-hop song.

| Instrument | Template | Highlights |
|------------|----------|------------|
| kick | kick.txt | `f0, sweep, rate, decay, click_*, sub_*, noise_*, eq_*, clip` |
| snare | snare.txt | `tone_amt, f1/f2, decay, noise_amt, ndecay, gates` |
| snarefill | snare.txt | same template, 16th-note roll `gates` (arranged into fills) |
| clap | clap.txt | `decay1/2, tone_*`, beat-gated on 2 & 4 |
| hat | hat.txt | `decay, hp` + `gates` (taps on the first two 16ths of each beat) |
| ohat | ohat.txt | offbeat (`off, win`), `decay, hp` |
| ride | ride.txt | inharmonic sines + noise, `gates` on quarters, HP 1.5 kHz |
| crash | crash.txt | noise burst, rings every `period` seconds |
| breakbeat | breakbeat.txt | kick + snare + hat `kgates/sgates/hgates`, `chop_*` stutter |
| shaker | shaker.txt | `decay, hp, gates` |
| conga | conga.txt | tuned hand drum: `pitches, gates, slap`, `sweep, rate, decay, hp, lpc, aecho` |
| reese | reese.txt | square + detune + sub through a resonant 24 dB LP; `beatgrid` notes |
| acid | acid.txt | 303: `notes, accents, bends, gates`; filter crossfade + resonant peak |
| lead_pwm | lead_pwm.txt | unison PWM pulse lead, `notes, gates` |
| lead_fm | lead_fm.txt | 2-op FM lead, `notes, gates`, `aphaser` |
| pad | pad.txt | detuned chord (`n1/n2/n3`), slow swell |
| stab | stab.txt | short detuned chord stab (`n1/n2/n3, gates`) |
| blow | blow.txt | a **breath of filtered noise** (a candle puff): `at, period, attack, decay, hp, lp_hi, peak_f/q/g` plus a stereo **ping-pong delay** (`dry_l/r`, `ltaps/ldec`, `rtaps/rdec`) |

**Template variants (per-instrument effects).** The mix-level `Effects` reverb is
applied to the *whole* mix, so an effect on a single stem is baked into that stem's
graph instead. `bass.txt` is the analogue bass schematic (`notes`, `amp1/2/3`,
`decay1/2`, `detune`, `sub_*`) used by the Hardgroove and Minimal tracks. Two
variants add effects:

- `kick_verb.txt` - `kick.txt` plus a **room send**: the dry kick is split and the
  wet branch is `aecho` taps (`verb1..3`, `vdec1..3`), high-passed (`verb_hp`) and
  mixed back at `verb`.
- `hat_rand.txt` - a **random** 16th-note hat: the noise burst is gated per step by a
  golden-ratio low-discrepancy sequence, `lt(mod(floor(t/step)*gold_step,1),prob)` -
  deterministic, so renders stay reproducible, and non-repeating across bars - with
  per-step velocity from a second sequence (`gold_vel`). The dry hat is split into a
  **delay** send (`del_ms`, `del_dec` taps) and a **room** send (`room_ms`,
  `room_dec`), each high-passed and returned at `del_mix`/`room_mix`.

Because `aecho` cannot null its dry path, a send uses a low `in_gain` (`0.1`) so the
wet branch carries only the tail; a delay with feedback is a multi-tap `aecho`
(e.g. `450|900|1350`), not a loop.

**Minimal-kit variants.** `hat_step.txt` is a gated noise hat whose hits come from a
`gates` list and whose accents come from a parallel `vel` list. `ohat_dyn.txt` is an
open hat with **dynamism**: each hit's *decay* is scaled by
`dmin + dspan*(0.5+0.5*sin(floor(t/step)*gold2))` and its *velocity* by
`vbase + vamt*(0.5+0.5*sin(floor(t/step)*gold))`. Both are indexed by the absolute
16th (`floor(t/step)`), so accents and ring lengths never settle into a fixed bar
loop - deterministic, but not periodic. `bass.txt` also takes `lp_q`, so its
low-pass is resonant (`lowpass=f=<lp_bass>:t=q:w=<lp_q>`); Hardgroove supplies
`lp_q=0.707` (its previous Butterworth response - byte-identical output) while
Minimal uses `lp_bass=320, lp_q=1.4` for a much deeper, resonant filter.

The **vox** stem is not a template: `fftechno/vox.py` synthesizes short phrases
with a local TTS and places them via `filters/<song>/vox.txt`; the same
`songs/<song>/vocals.md` times are written to `output/<song>/lyrics.json` for the
on-screen lyrics. Three engines exist (chosen by `engine:` in `vocals.md`, or
`--tts`): **Kitten TTS** (`kittenml` + the nano ONNX model), **Piper**
(`tools/piper`), and **`flite`** - FFmpeg's own built-in TTS (libflite, voices
`slt`, `kal`, `kal16`, `rms`, `awb`), which needs no model files or network at all.
The TTS pads leading silence
onto every phrase (about 0.65 s for Kitten, 0.15-0.29 s for flite), so `vocals.md`
can set `trim_lead: 1` to strip it before placement and have the phrase start
exactly on its time (it has no other effect on the phrase); `minimal`'s parked
"tick" count-in uses it, and it fixes the same lateness in any song.
The stem is mixed through the `Levels` table like any other (`vox`), so its timing
is free of the section automation. A song with no `vox` in its Stems table has no
vocal: `audio.build` also deletes a stale `lyrics.json`, so the video never draws
lines for a voice that is not in the mix.

**Losslessness.** The generated graphs reproduce the original hand-authored
expressions value-for-value (verified: rendering each stem against its original
differs only by float rounding, <= -213 dB).

## 9. Mix specification - `fftechno/arrangement.py`

`build_graph(song)` emits, in `Stems` order:

- per arranged stem: `[i]volume=volume='<boost>*<nested if(lt(t,..))>':eval=frame[stemv]`
  followed by a `pan=stereo|...` to `[stem]`; the final section fades over
  `fade_bars`;
- per `Levels` stem: `[i]volume=<level>[<stem>v]` followed by that stem's `Pan` row -
  a non-arranged stem is placed exactly like an arranged one (it used to be folded to
  mono centre, ignoring the `Pan` table);
- `[<sidechain_key>]asplit=2[keym][sckey]`;
- `[<low_bus>]amix=inputs=N:normalize=0[low]`;
- `[low][sckey]sidechaincompress=threshold=..:ratio=..:attack=..:release=..[lowd]`;
- `[lowd][<other stems>]amix=inputs=..:normalize=0[sum]`;
- reverb send: `[sum]asplit -> [sr]highpass=f=<reverb_hpf>,volume=<reverb_send>` then
  `afir=dry=0:wet=<reverb_wet>:gtype=peak` with the IR as the last input;
- bus: `[sum][rvb]amix -> extrastereo=m=<stereo_width> -> acompressor=...`.

The graph is written to `output/<song>/logs/mix.txt`.

## 10. Master specification - `fftechno/audio.py`

Two passes: `loudnorm` in measurement mode, then a linear apply.

```
[0]loudnorm=I=-13.0:TP=-1.0:LRA=11:measured_I=..:measured_TP=..:measured_LRA=..
   :measured_thresh=..:offset=..:linear=true,
   alimiter=limit=0.88:level=disabled,
   equalizer=f=9000:t=h:w=0.7:g=1.5,
   aresample=48000:out_sample_fmt=s16:dither_method=triangular_hp,
   aformat=sample_fmts=s16:channel_layouts=stereo
```

`alimiter` must use `level=disabled` (its auto-level would boost over the ceiling).
With `--safe` (off by default) a second, stricter `alimiter` (`limit=0.5`, about
-6 dBFS) is inserted for ear protection.

## 11. Output format

`output/<song>/techno.wav`: pcm_s16le, 48 kHz, 2 channels. The length is `bars`
times one bar (`240/bpm` seconds): 240 s for `basement`, `hardgroove` and
`triphop`, 180 s for `minimal`, about 21.8 s for `triphop_beat`. The master
targets -13 LUFS and -1 dBTP.

## 12. Video - `visualizer.vpy`

VapourSynth + vs-placebo. The picture is produced by a **source** (`Look`) and an
ordered **effect chain** (`fftechno/effects.py`, see 12.5). A small piece of
per-frame data is written into a low-res YUV444P16 clip (half the output size;
960x540 at the default 1920x1080) and upscaled to that size. Paint-tier effects
draw into that frame and shader-tier effects are
spliced into a GLSL shader that reads the picture (`HOOKED_tex`), the audio data
strip and `frame` (time). The shader **preserves chroma** (so the blue hair stays
blue). Output is YUV420P8, piped to ffmpeg by `vspipe -c y4m`. `--static` renders a
single frozen frame.

Environment inputs: `FFTECHNO_AUDIO` (the mastered WAV), `FFTECHNO_W` / `FFTECHNO_H`
(the output size - a song can be vertical, e.g. `size: 1080x1920` in `video.md`),
`FFTECHNO_GIRL_FRAMES` (grey frame stack - edge/pollock), `FFTECHNO_GIRL_SPRITES` +
`FFTECHNO_GIRL_PICK` (RGB sprites + per-frame index - outline/photo),
`FFTECHNO_POLLOCK` (paint-accumulation mode), `FFTECHNO_FX` (the effect-chain JSON),
`FFTECHNO_ENV_DIR` (the per-instrument envelopes), `FFTECHNO_ROOT` (so the script can
import `fftechno.effects`) and `FFTECHNO_STATIC`. With no picture data at all it
falls back to ASCII art of any `ascii/*.jpg|png`.

The output size drives everything downstream: the picture-data frame is half the
output (`GW, GH = W/2, H/2`), the audio data strip sits in its top 4 rows, the 720p
preview keeps the aspect (720x1280 when vertical) and the shader's strip row
coordinates are built for that height (`assemble_shader(..., height)`).

### 12.1 Girl pipeline - `fftechno/girl.py` (+ `fftechno/matte.py`)

1. `source_clip()`: the first video in `ascii/`.
2. Decode `GIRL_CROP_START .. +GIRL_CROP_DURATION` (2.0 s..5.0 s) at native size/fps.
3. Per look:
   - **edge**: `RVMMatte` -> alpha; `largest_component` keeps the subject (drops
     the crowd); composite over black; `edgedetect` (white lines on black).
   - **pollock**: skip the matte; whole frame -> `gblur` -> `edgedetect` -> two
     crossed rotated copies blended (`rotate` + `blend=lighten`).
   - **outline**: `RVMMatte` -> fine alpha; `largest_component` picks the subject
     (crowd removed; the top truss margin is ignored); draw the **silhouette
     contour only** (`dilate(subj) & ~subj` - no interior/face lines) in white,
     plus the **blue hair chroma-keyed** from the source RGB.
4. ffmpeg/numpy: `fps=30`, fit to 16:9 with black bars (`scale`+`pad`), then the look.
5. Emit `output/<song>/girl_loop.mp4` (silent, versioned) and the frame data -
   `girl_frames.npy` (edge/pollock) or `girl_sprites.npy` + `girl_pick.npy`
   (outline).

### 12.2 Pollock accumulation - the three modes

The frame stack holds the per-frame *stroke layer*; the visualizer accumulates it
into a running paint canvas (`max`-blend with decay), then adds fresh random
splatter (never accumulated) each frame:

| `--mode` | Behaviour | Decay/frame |
|----------|-----------|-------------|
| `reset` | clears at every loop boundary (a fresh canvas per phrase) | 0.90 |
| `trail` | short-lived streaks (default) | 0.85 |
| `build` | long-lived, densely builds up | 0.995 |

### 12.3 Outline look - beat-synced stills

`outline` builds one RGB sprite per source frame (white silhouette contour + blue
hair on black), then a per-output-frame index (`girl_pick.npy`) that picks a
random sprite held for exactly one beat - the BPM is read from `song.md`, so the
picture strobes in time with the track. The visualizer writes Y/U/V from the
sprite so the colour survives the shader.

### 12.4 On-screen lyrics

The visualizer reads `output/<song>/lyrics.json` (`[[text, start], ...]`, written
by `vox.py` from the song's `vocals.md`, the same list that places the vocal audio) and
draws each line for `LYRIC_DUR` seconds near the bottom using a self-contained 5x7
uppercase bitmap font - no font file, no libass/fontconfig.

### 12.5 Effects - `fftechno/effects.py`

The picture is produced by a **source** (`Look`) plus an ordered **effect chain**:

```
source  ->  effects (paint: numpy per frame | shader: GLSL per pixel)  ->  encode
```

An `Effect` declares `name`, `tier`, `uses_strip`, `defaults`, `required_instruments()`,
`prepare(env, fps)`, `paint(ctx)` and/or `glsl_helpers()` + `glsl_apply()`:

| tier | runs | effects |
|------|------|---------|
| `paint` | numpy, per frame, on the 960x540 frame | `squares` |
| `shader` | GLSL spliced into the vs-placebo shader (1920x1080) | `grain`, `vignette`, `kick_flash`, `kick_glitch` |

The chain is `effects: a, b, c` in `video.md` (comma list, spaces allowed) or
`--fx a,b` on the CLI; unknown names raise. Per-effect knobs live in the same
`## Parameters` table (`| name | key | value |`, where *name* is a look **or** an
effect). The built-in default chain (`kick_flash, vignette, grain, kick_glitch`)
reproduces the original hand-written shader, so a song that names no effects renders
as before - verified by frame hash (the only variation is the shader's own grain
jitter, `<= 4/255`, which predates this and also affects repeat renders).

`assemble_shader()` splices each shader effect's helpers before `hook()` and its
apply statements inside it, in chain order. The audio data strip - and the row mask
that hides it - is only emitted when some effect has `uses_strip`, so a strip-less
chain does not blank the top of the picture.

**Instrument reactivity.** `video.py` asks the chain which instruments it needs
(`required_instruments`) and bakes each into `logs/fx/<stem>.wav`, applying that
stem's `Sections` automation from `song.md` (`arrangement.gain_expr`) first - so a
visual follows the arrangement: the snare's square is absent while its section gain
is `0.00`. The visualizer loads those as per-frame RMS envelopes
(`effects.load_envelopes`) and passes them to `prepare()`.

`squares` draws one white outline per instrument - concentric, largest outermost -
and drives a single parameter each (`ROLES`): size, vertical drift, line thickness,
rotation, a horizontal knock or a brightness flash. Instruments listed in `circles`
(`rim` by default) are drawn as a **ring** instead of a square, so the rim shot is a
circle at the centre of the pattern; a ring pings by growing, since a brightness
blink would need it to sit below white. `halves` gives the sizes explicitly, in
instrument order, so a composition can be designed (e.g. put the ring around the
subject's face with squares both outside and inside it); `skip` leaves instruments
out (`vox` by default - the voice is already on screen as the lyric). A shape is
shown only while its instrument is audible: a slow release follower (`presence`
seconds) is compared against `presence_on`, and while muted the shape is **hidden,
never dimmed** - the drawn level is `level` (1.0 = pure white). A square can never
grow past the frame (a cap derived from the smaller dimension), and each shape is
rasterised inside its own bounding box, so the cost is independent of the frame
area.

**Picture framing** (`photo`). The still-photo source can either `fit` (keep the
whole image, letterbox on black - good for a landscape frame) or `fill` (scale to
cover the frame and centre-crop). `focus` names the vertical fraction of the image that
must land in the middle of the frame (the subject's nose at `0.324` for `minimal`'s
current still): the cropped window is symmetric about it and as large as the aspect and
the image allow, so the framing stays as wide as possible while the chosen point sits at
the centre - which is also where the ring is drawn. It is how a wide 16:9 still is
zoomed so a face lands at the centre of the pattern. `shift_x` / `shift_y` nudge the
subject within the frame, in *output* pixels (positive = right/down), by moving the crop
window the other way. `crop_bottom` / `crop_right` trim a fraction off the bottom or the
right first (e.g. a watermark - the current still's sits at x 0.88-0.925 / y 0.843-0.857).

## 13. Verification and acceptance

| Check | Method | Result |
|-------|--------|--------|
| Template losslessness (hardgroove port) | render each stem vs its original | <= -213 dB (float noise) |
| Filter graphs valid | `ffmpeg -/filter_complex` per stem | clean |
| Loudness | `ebur128` | -13.0 LUFS |
| True peak | `ebur128=peak=true` | -1.0 dBFS |
| Safe mode | `ebur128` with `--safe` | true peak about -6 dBFS |
| Video | `ffprobe` + spot frames | 1920x1080, 30 fps, lyrics on time |
| Determinism | rebuild the ffmpeg stems | identical |

## 14. Reproducibility

`python -m fftechno audio` regenerates `filters/*.txt`, the stems, the mix and the
master from markdown alone. The ffmpeg synthesis is deterministic for a fixed
build; the neural-TTS voice is deterministic for a given model. The build lock
guarantees a single writer.

## 15. Requirements and environment

- **ffmpeg 9+ / ffprobe** (gyan.dev full build). Audio filters: `aevalsrc`,
  `asubboost`, `asoftclip`, `acrusher`, `equalizer`, `highpass`, `lowpass`, `asplit`,
  `amix`, `pan`, `haas`, `extrastereo`, `sidechaincompress`, `acompressor`,
  `alimiter`, `loudnorm`, `afir`, `aresample`, `aformat`, `adelay`, `apad`, `volume`
  (`eval=frame`). Video filters: `edgedetect`, `format`, `fps`, `scale`,
  `pad`. Filtergraphs are read from files with `-/filter_complex FILE`
  (`-filter_complex_script` was removed in ffmpeg 8/9).
- Python 3.10+ (most tooling is the standard library; the video needs the venv
  above and the voice needs `kittenml` or Piper).
- Video: venv with `vapoursynth`, `numpy`, `vs-placebo` (`vspipe`) and a Vulkan GPU.
  Run `.venv\Scripts\python -m vapoursynth config` once (the `Scripts\vapoursynth`
  launcher needs a configured shell).
- Isolation: `onnxruntime` plus the RVM ONNX model (~15 MB) under `tools/rvm/`:

  ```powershell
  .venv\Scripts\pip install onnxruntime
  curl -L -o tools\rvm\rvm_mobilenetv3_fp32.onnx https://github.com/PeterL1n/RobustVideoMatting/releases/download/v1.0.0/rvm_mobilenetv3_fp32.onnx
  ```
- Vocals: a local neural TTS (offline):
  - **Kitten TTS** (default): `pip install kittenml soundfile huggingface_hub
    phonemizer espeakng_loader` (no torch needed; the nano ONNX model is fetched
    to `tools/kitten/`).
  - **Piper**: unzip the Windows build into `tools/piper/` and put a voice
    (`<name>.onnx` + `.onnx.json`) in `tools/piper/voices/`.

## 16. Troubleshooting / FAQ

- **Silence or a thin mix?** A stem WAV may be truncated (two builds overlapping).
  Re-run `python -m fftechno audio`; the build lock prevents overlap.
- **"another fftechno build is running"?** A lock file exists; wait, or delete
  `output/<song>/logs/.build.lock` if stale.
- **A template error?** `synth` names the missing value.
- **Where are logs?** `output/<song>/logs/` (`vspipe.log`, `ffmpeg_video.log`,
  `mix.txt`).
- **Noncommercial?** Yes - PolyForm Noncommercial 1.0.0 (`LICENSE.md`).

## 17. Extension guide

- **Tempo/length:** edit `bpm`/`bars` and the `Sections` rows. `bar`, `step`,
  `beat` and `dur` follow `bpm` and `bars`. Do not copy them into `sounds.md`.
- **New instrument:** add a `templates/<name>.txt` (with `{{keys}}`), a row in
  `sounds.md`, the name in the `Stems` table, a `Pan` row, and either a `Boosts`
  row plus a `Sections` column, or a `Levels` row.
- **New sampler (sample-based instrument):** fetch the sample
  (`python -m fftechno samples`, section 21), add a row to the song's `## Samplers`
  table (`name | sample | params`), then list the name in `Stems` with a `Pan` row
  and a `Boosts`+`Sections` (or `Levels`) entry - the mix side is identical to a synth
  stem.
- **New song:** add `songs/<name>/song.md` and `sounds.md` (optionally `vocals.md`,
  `video.md`). A folder is the song. There is no subclass and no registry.
- **Per-instrument effect (reverb/delay):** add a template variant that splits the
  stem and mixes an `aecho` wet branch back in (see `kick_verb.txt`, `hat_rand.txt`).
- **New visual effect:** add a class in `fftechno/effects.py` (paint tier for
  geometry, shader tier for per-pixel work) and name it in the song's `video.md`
  (`effects: squares, grain`); knobs go in that song's `## Parameters` table.
- **New picture source:** add a `Look` in `fftechno/looks.py` and set `look:` in
  `video.md` (`edge`, `pollock`, `outline`, `photo`).
- **New step melody:** use `{{if_steps(seq; grid; default)}}` and a `\|` list.
- **Mix effects:** the `Effects` table.
- **Video:** name effects in `video.md` (`effects:`). The shader is assembled from
  that chain (`effects.assemble_shader`). Do not edit a `SHADER` constant.

## 18. File inventory

```
songs/<name>/                control surfaces: song.md, sounds.md (+ optional
                             vocals.md, video.md)
templates/*.txt              synth schematics: the techno set, its variants
                             (kick_verb, hat_rand), the trip-hop set, and examples
                             (sax, rhodes, beeps, growl, rim, tom)
filters/<name>/*.txt         generated graphs + vox.txt
fftechno/                    config, md, song, looks, effects, proc (build lock),
                             audio, synth, sampler, samples, arrangement, vox, girl,
                             matte, video, cli
samples/                     manifest.md (tracked) + downloaded sample sets
                             (gitignored): triphop_kit/, breaks/
visualizer.vpy               the video
pyproject.toml LICENSE.md README.md SPEC.md TODO.md CHANGELOG.md
                             AEVAL_TUTORIAL.md (the aevalsrc/aeval guide)
output/<name>/               techno*.wav, techno_visualizer*.mp4, girl_loop*.mp4,
                             girl_frames.npy / girl_sprites.npy + girl_pick.npy,
                             lyrics.json, stems/, logs/
tools/ ascii/                RVM + voice models + the source clip
```

## 19. Risks and limitations

- ffmpeg `eval` has no user variables, so constants repeat inside expressions.
- `loudnorm` runs at 192 kHz internally; the following `aresample=48000` is required.
- `random()` noise is deterministic for a fixed ffmpeg build, but a different build
  may change the noise timbre.
- VapourSynth scripts are Python by definition; the video layer needs the venv.

## 20. Songs and looks

The code is song-agnostic; song data lives in folders and the style-specific video
code lives in one place.

**Tracks.** `basement` (155 BPM jungle techno, 155 bars, 16 instruments + vox,
`outline` video). `hardgroove` (140 BPM, 140 bars, 12 instruments + vox in Levels,
`edge` video). `minimal` (100 BPM, 75 bars = 3:00, Robert-Hood-style: a dry,
never-dropping 4-on-4 kick, closed + dynamic open hats, snare, rim and a one-note
bass under a resonant low-pass). A single **`blow`** stem - a candle puff of
filtered noise (`templates/blow.txt`, `period`-repeated) - is panned right and
repeats every two bars from the 2:00 mark to the end of the track (13 puffs of
~0.26 s), fading with the outro. The track is **instrumental**: a "tick" count-in
is written in `songs/minimal/vocals.md` (engine `flite`) but parked - `vox.py`
only renders when `vox` is in the song's Stems table, and `audio.build` drops a
stale `lyrics.json` so the video cannot draw a voice that is not in the mix. Its
video is **1920x1080** (no `size:` line). The still photo is framed with `focus`
so the subject's nose sits at the centre of the pattern, with the `squares, grain`
chain. `triphop` (84 BPM, 84 bars = 4:00, instrumental, audio only) uses kick,
brk, roll, sub, ep, strings, bell, stab, horn, rise and vinyl. The side-chain key
is kick and the low bus is sub. The master on disk is `output/triphop/techno_v4.wav`.
`triphop_beat` is an 88 BPM, 8-bar scratch (kick, break, bass), not the 4-minute song.
`triphop_samples` is the **sample-based** counterpart: 88 BPM, 8 bars, the TR-909 SP
kit (`samples/triphop_kit/`) under a slowed Amen break (`samples/breaks/amen.wav` at
`rate=0.81`) - see section 21.

**Songs** (`fftechno/song.py`). `Song(name)` exposes a track: paths to its four
markdown files; its `filters`/`output`/`stems`/`logs` dirs; its parsed
arrangement; derived `bpm`/`bar`/`duration`; its `vocals()` (TTS engine/voice +
phrase times) and `video()` (source, crop, look, loop, size, effect chain); and
per-song output paths (`techno.wav`, `techno_visualizer*.mp4`, `girl_*`,
`lyrics.json`). `names()` is the directory names under `songs/`. `load(name)`
returns `Song(name)`. Adding a track = add `songs/<name>/` with `song.md` and
`sounds.md` (`vocals.md`/`video.md` are optional - without them the song is
instrumental with no video).

**Looks** (`fftechno/looks.py`). `girl.py` is a generic pipeline (decode ->
optional matte -> look -> fit -> emit); a `Look` strategy declares `needs_matte`,
`emits` (`stack` grey frames or `sprites` RGB), an optional `accumulation` hint and
`decode` (`native`/`fitted`), plus `stack_filter(w,h)` (a `-filter_complex` body)
and/or `sprites(frames, model)`. Four are registered: `edge`, `pollock`,
`outline`, `photo`. Adding a look = one subclass (and, if it needs knobs, a
`| name | key | value |` row in a song's `video.md`).

`templates/`, `filters/<song>/`, `visualizer.vpy` and the models in `tools/` are
shared across every song.

## 21. Sample-based songs - `samples/` + `fftechno/sampler.py`

A song can make its sound from **audio files** instead of `aevalsrc` oscillators. This
section is the whole of the sample support.

**The store.** `samples/manifest.md` (tracked) lists every sample as
`| set | file | url | license |`. `python -m fftechno samples` downloads the missing
files to `samples/<set>/<file>` and normalises each to a 48 kHz PCM WAV (which also
removes the malformed trailing packet some 24-bit sources carry - the cause of the
benign `Invalid PCM packet` log line). The downloaded files are **not** committed
(`.gitignore` keeps only `manifest.md`); a clone reproduces them from the manifest.
`fftechno/samples.py` holds `fetch`/`prepare`/`run`.

**The instrument.** A `## Samplers` table in `sounds.md` (`| name | sample | params |`)
names a sample and how it plays. `synth.generate` calls
`sampler.graph(song, sample, params)` and writes `filters/<song>/<name>.txt` - the same
node type as a synth stem, so `audio.render_stems` -> mix -> master is unchanged.

The generated graph reads the file with the `amovie` source filter (a `filter_complex`
source, so no `-i` is needed), fans it out with `asplit` (one branch per hit) and places
each copy on the grid with `adelay`; `amix` (with a silent bed of the full song length)
sums them, so the stem is always exactly `song.duration`. Because `render_stems` passes
**repo-relative** `samples/...` paths to `amovie`, it runs ffmpeg with the repo root as
its working directory (`proc.run(cwd=...)`); otherwise the path would not resolve.

Parameters (comma separated `key=value`):

| key | meaning |
|-----|---------|
| `pat` | 16th steps (0-15) inside one bar, repeated on every bar |
| `hits` | absolute 16th steps from the song start (sparse sounds, e.g. a break every two bars) |
| `vel` | per-hit velocity, parallel to `pat`/`hits` |
| `trim` | seconds each copy plays (default: the whole file) |
| `rate` | `asetrate` varispeed factor (below 1 = slower and lower) |
| `tempo` | `atempo` factor (changes speed, keeps pitch) |
| `gain` | per-instrument gain |

Use `pat` **or** `hits`, not both. Every hit is placed by an **absolute** `adelay`
(milliseconds), so there is no cumulative drift and the onsets land on the grid
(measured within ~0.3 ms). Loop filters (`aloop`) are deliberately *not* used - they
proved unreliable at this grid. The one cost is that a long song expands to one filter
chain per hit (`bars` x hits per bar): fine for a beat, a note for a 4-minute track.

Example (`songs/triphop_samples/sounds.md`):

```
| name | sample                             | params |
|------|------------------------------------|--------|
| kick | samples/triphop_kit/kick.wav       | pat=0\|6\|10, gain=1.0, trim=0.6 |
| brk  | samples/breaks/amen.wav            | hits=0\|32\|64\|96, rate=0.81, gain=0.75, trim=5.4545 |
```
