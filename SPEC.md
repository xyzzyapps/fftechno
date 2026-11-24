# SPEC.md - fftechno (SRS)

Technical specification of **fftechno**: underground tracks synthesized by
**ffmpeg**, plus a music video when the song has one. A song is a folder under
`songs/`: `basement` (155 BPM, 155 bars, 4:00), `hardgroove` (140 BPM, 140 bars,
4:00), `minimal` (100 BPM, 75 bars, 3:00), `triphop` (84 BPM, 84 bars, 4:00, audio
only), `triphop_beat` (88 BPM, 8 bars, a scratch), `triphop_samples` (84 BPM, 80
bars, 3:48.6; sample-based: Amen break + sub + electric piano + vinyl; the delivered
cut is 3:42.9), `oldschool_acid` (132 BPM, 132 bars, 4:00, oldschool acid techno),
`psych` (110 BPM, 110 bars, 4:00, 1960s psychedelic rock with a wall
of sound), `warpainting` (79 BPM, 158 bars, 8:00, psychedelic drone rock),
`stoner` (76 BPM, 76 bars, 4:00, stoner rock) and `stoner_samples` (80 BPM,
80 bars, 4:00, sampled stoner rock). A voice, when the song has a `vox` stem, comes
from a local neural TTS. The build tooling is Python. The arrangement and every
instrument parameter live in markdown. The repository also ships the one-page
technique card `docs/ffmpeg_cheatsheet.png` and its generator.

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

## 3. Song constants

There are no build-wide musical constants: `bpm` and `bars` come from each song's
`song.md`. The table below is the default song, `basement`, and shows the shape of the
derived clock. Every other song substitutes its own values.

| Name | Value (basement) |
|------|------------------|
| BPM | 155 |
| bars | 155 (4:00) |
| sample rate | 48000 Hz (oscillators generated at 192000 Hz, then downsampled) |
| loudness target | -13 LUFS, true peak -1.0 dBFS |
| stems | kick, snare, snarefill, clap, hat, ohat, ride, crash, breakbeat, conga, shaker, reese, acid, lead_pwm, lead_fm, pad, stab, vox |

Derived: `beat = 60/155 = 0.387097 s`, `step (16th) = 0.096774 s`,
`bar = 1.548387 s`. In general the song length is `bars * 240/bpm`; for example
`triphop_samples` is `80 * 240/84 = 228.571 s`, and `triphop_beat` is
`8 * 240/88 = 21.818 s`.

## 4. Architecture and data flow

```
  songs/<song>/song.md (arrangement)     songs/<song>/sounds.md + templates/
      |  arrangement.py                            |  synth.py
      v                                            v
  mix filtergraph                              filters/<song>/<name>.txt
  (<out>/<song>/logs/mix.txt)                        |
      |                                              |  audio.render_stems()
      |                                              v
      |                               <out>/<song>/stems/<name>.wav  (+ vox.wav)
      +--------------------+-------------------------+
                           v
              mix  ->  <out>/<song>/mix_pre.wav
                           v
              master (2-pass loudnorm)  ->  <out>/<song>/techno.wav
                           v
              songs/<song>/video.md -> Look (picture) + effect chain (effects.py)
                           v
              output/<song>/girl_loop.mp4
              + girl_frames.npy  /  girl_sprites.npy + girl_pick.npy
              + logs/fx.json + logs/fx/<stem>.wav (gain-applied envelopes)
                           v
              vspipe fftechno/visualizer.vpy (paint + shader) -> ffmpeg -> techno_visualizer.mp4
```

Sample-based songs replace the template branch with
`samples/manifest.md -> python -m fftechno samples -> samples/<set>/*.wav ->
sampler.graph`. The optional `audio --out DIR` flag changes the output root from
`output/` to `DIR` (for a clean audit build, e.g. `--out out2`); `filters/` is
generated and gitignored, and stays in the repo for all output roots.

## 5. Build pipeline

Commands (`python -m fftechno ...`):

Every command except `samples` takes `--song <name>` (default `basement`).

| Command | Phases |
|---------|--------|
| `synth --song S` | `songs/S/sounds.md` + `templates/` -> `filters/S/<name>.txt` (generated, gitignored; oscillator templates and sampler graphs) |
| `samples [--force]` | `samples/manifest.md` -> download + normalise the files under `samples/` (no `--song`) |
| `audio --song S [--out DIR] [--safe] [--tts kitten\|piper\|flite]` | `synth` -> IR -> vocals -> stems -> mix -> master -> `<out>/S/techno.wav` |
| `girl --song S [--look edge\|pollock\|outline\|photo] [--mode reset\|trail\|build]` | picture source -> look -> `output/S/girl_loop.mp4` + picture data |
| `video --song S [--look ..] [--fx a,b] [--mode ..] [--boost F] [--static]` | envelopes -> render -> mux -> 720p preview -> optional re-level |
| `all --song S [--look ..] [--fx a,b] [--mode ..] [--safe] [--tts ..] [--boost F] [--static]` | `audio`, then `girl`, then `video` |
| `boost F --song S` | re-encode the MP4 audio at gain `F` (video copied) |
| `swap --song S` | replace the MP4 audio with the current master (video **copied** - the way to apply an audio-only change) |

`--out DIR` applies to `audio` only; it resolves `DIR` and redirects
`song.output`/stems/logs/the master there. It is useful for a clean verification
run without adding a `_vN` to the normal `output/` tree.

Filtergraphs are read from files with the ffmpeg 9 syntax `-/filter_complex FILE`
(the old `-filter_complex_script` was removed).

Outputs are written with `config.unique_path`: if the target exists, the build
writes `name_v2.ext`, `_v3`, ... so existing renders are never overwritten.

A **build lock** (`<out>/<song>/logs/.build.lock`, created with `O_EXCL`) prevents
two builds writing the same outputs concurrently; a second run exits with a clear
message.

## 6. Control surface A - `songs/<name>/song.md`

Scalars (all required):

```
bpm: 155
bars: 155
fade_bars: 7            # the final section fades to silence over this many bars
sidechain_key: kick     # which stem drives the ducking
low_bus: reese          # stems grouped and ducked under the key
reverb_seconds: 5.5     # optional convolution-reverb IR length (default 2.2)
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
  `bus_threshold/ratio/attack/release`. Optional master overrides:
  `master_eq_f`, `master_eq_g`, `master_eq_w`, `master_limiter`.
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
- Templates may be written over several indented lines. Blank lines and full-line
  `#` comments are ignored; the remaining lines are joined with a single space
  before substitution. Line breaks and indentation are insignificant, but a line
  must not split a token.
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
`sounds.md`). The table below also lists `blow`, which `minimal` uses. The synthesis
techniques behind these templates are described in
[`docs/SOUND_DESIGN.md`](docs/SOUND_DESIGN.md). Template
*variants* that add per-instrument effects are listed after the table. `triphop` adds `boom.txt`, `break_sp.txt`, `roll.txt`, `sub.txt`,
`ep.txt`, `strings.txt`, `bell.txt`, `dubstab.txt`, `horn.txt`, `rise.txt` and
`vinyl.txt`. `triphop_beat` uses `break_synth.txt`, `kick_trip.txt` and
`bass_gate.txt`. `triphop_samples` uses `ep.txt` plus `sub_async.txt` (a bar-long, punched, drifting
melody); its vinyl is a sampler row, not a template. `sax.txt` and `rhodes.txt` are examples. They are not in the
shipped trip-hop song. `psych` adds `guitar_fuzz.txt`, `guitar_lead.txt`,
`organ.txt`, `bass_rock.txt` and `tamb.txt`; its drums reuse `kick_trip.txt`,
`snare.txt`, `tom.txt`, `hat_step.txt`, `ride.txt` and `crash.txt`, and its wash
reuses `pad.txt`. `stoner` adds `guitar_wah.txt` and reuses `guitar_fuzz.txt`,
`bass_rock.txt`, `organ.txt` and the drum templates.

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
| acid | acid.txt | 303: `notes, accents, bends`; filter crossfade + resonant peak |
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
- `acid_303.txt` - the 303 with a per-step gate and a short attack before the decay;
  `oldschool_acid` uses it for a 32-step (two-bar) gated phrase.

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
`vocals.md` may also have a `## Parameters` table (`| key | value |`) for the voice
treatment: `pitch`, `speed`, `highpass`, `mid_f`, `mid_g`, `low_f`, `low_g`,
`drive`, `echo`, `lowpass`, `volume`, `trim_db` and `trim_silence`. The defaults
live in `vox.VOICE_DEFAULTS`; the shipped songs use them unchanged.
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
   alimiter=limit=<master_limiter>:level=disabled,
   equalizer=f=<master_eq_f>:t=h:w=<master_eq_w>:g=<master_eq_g>,
   aresample=<master_sr>:out_sample_fmt=s16:dither_method=triangular_hp,
   aformat=sample_fmts=s16:channel_layouts=stereo
```

The defaults are `config` constants (`MASTER_SR`, `MASTER_EQ_F`, `MASTER_EQ_G`,
`MASTER_EQ_W`, `LIMITER_CEILING`). A song can override the master EQ and limiter in
its Effects table with `master_eq_f`, `master_eq_g`, `master_eq_w` and
`master_limiter`.
`alimiter` must use `level=disabled` (its auto-level would boost over the ceiling).
With `--safe` (off by default) a second, stricter `alimiter` (`limit=0.5`, about
-6 dBFS) is inserted for ear protection.

The convolution IR is generated by `audio.make_ir`: decaying stereo noise whose
length is the song's optional `reverb_seconds` (default 2.2; `psych` sets 5.5,
`stoner` 5.0). The
decay rate scales with the length, so the default expression is byte-identical to
before.

## 11. Output format

`<out>/<song>/techno.wav`: pcm_s16le, 48 kHz, 2 channels. The length is `bars`
times one bar (`240/bpm` seconds): 240 s for `basement`, `hardgroove`, `triphop`,
`psych`, `stoner` and `stoner_samples`; 180 s for `minimal`; 228.571 s for
`triphop_samples` (80 bars at 84 BPM); and 21.818 s for `triphop_beat`. The
delivered `triphop_samples` cut trims the first two bars (5.714286 s), so its
master and YouTube video are 222.857 s. The master targets -13 LUFS and -1 dBTP.

## 12. Video - `fftechno/visualizer.vpy`

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
`FFTECHNO_FPS` (the frame rate; defaults to `config.VIDEO_FPS`),
`FFTECHNO_GIRL_FRAMES` (grey frame stack - edge/pollock), `FFTECHNO_GIRL_SPRITES` +
`FFTECHNO_GIRL_PICK` (RGB sprites + per-frame index - outline/photo),
`FFTECHNO_POLLOCK` (paint-accumulation mode), `FFTECHNO_FX` (the effect-chain JSON),
`FFTECHNO_ENV_DIR` (the per-instrument envelopes), `FFTECHNO_LYRICS` (the lyric JSON,
when present), `FFTECHNO_ROOT` (so the script can import `fftechno.effects`) and
`FFTECHNO_STATIC`. With no picture data at all it falls back to ASCII art of any
`ascii/*.jpg|png`.

The output size drives everything downstream: the picture-data frame is half the
output (`GW, GH = W/2, H/2`), the audio data strip sits in its top 4 rows, the 720p
preview keeps the aspect (720x1280 when vertical) and the shader's strip row
coordinates are built for that height (`assemble_shader(..., height, fps)`). The
same FPS is passed into the shader, so its clock and the visualizer cannot drift.

### 12.1 Girl pipeline - `fftechno/girl.py` (+ `fftechno/matte.py`)

1. `source_clip()`: the configured `video.source`; otherwise the first video in
   `ascii/` (or, for `photo`, the first image). An empty `source:` is not treated
   as the repo root.
2. Decode `video.crop_start .. + video.crop_duration` (default 2.0 s..5.0 s) at
   native size/fps. A still image has no timeline, so it is decoded once.
3. Per look:
   - **edge**: `RVMMatte` -> alpha; `largest_component` keeps the subject (drops
     the crowd); composite over black; `edgedetect` (white lines on black).
   - **pollock**: skip the matte; whole frame -> `gblur` -> `edgedetect` -> two
     crossed rotated copies blended (`rotate` + `blend=lighten`).
   - **outline**: `RVMMatte` -> fine alpha; `largest_component` picks the subject
     (crowd removed; the top truss margin is ignored); draw the **silhouette
     contour only** (`dilate(subj) & ~subj` - no interior/face lines) in white,
     plus the **blue hair chroma-keyed** from the source RGB.
4. ffmpeg/numpy: `fps=30`, fit the output frame (letterbox for `edge`/`pollock`,
   or `fit`/`fill` for `photo`), then apply the look.
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
rotation, a horizontal knock or a brightness flash. `roles` overrides the mapping
(`kick:thickness|snare:knock|...`) and `order` sets the outer-to-inner instrument
order; both default to the built-in techno mapping. Instruments listed in `circles`
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

**Look thresholds.** The look-specific constants are also `video.md` parameters:
`edge_low` / `edge_high` for `edge`; `blur`, `edge_low`, `edge_high`, `rotate_a`
and `rotate_b` for `pollock`; and `top_margin`, `hair_gain`, `blue_min`, `blue_r`
and `blue_g` for `outline`. Their defaults preserve the shipped renders.

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

### 12.6 Cover video (the YouTube cut)

`triphop_samples` has no `video.md`. Its YouTube cut is a separate still-art ffmpeg
pass, not a `python -m fftechno video` render:

1. The square cover art is scaled to 1080x1080 (Lanczos) and centred.
2. A copy of the cover is scaled/cropped to 1920x1080, blurred (`gblur=sigma=45`)
   and darkened/desaturated (`eq=brightness=-0.22:saturation=0.85`) for the
   background.
3. The cover is overlaid at the centre.
4. A 1 s fade-in and a 2 s fade-out (`st=220.857`) are applied, then H.264 High
   (`-crf 18`, `yuv420p`, 30 fps) and AAC 320 kbps 48 kHz stereo are muxed with
   `+faststart`.

Delivered file: `output/triphop_samples/ASYNCHRONOUS_1080p.mp4`, 222.857 s,
1920x1080, 30 fps, 12,984,773 bytes. The cover carries vertical **XYZZY** in
Times New Roman with a multi-colour RGB-split glitch (cyan/red/magenta/green/yellow
ghosts, a white core and grain), centred. `cover_v1.jpg` is the clean art;
`cover.jpg` is the glitched version used by the video.

### 12.7 Cheat sheet

`docs/ffmpeg_cheatsheet.png` is a 1080x1350 social card listing the synthesis,
sequencing, filter, sampler, mastering, video and check techniques this project
uses. `docs/make_cheatsheet.py` draws it with Pillow and the Windows system fonts
(Times New Roman for the title, Consolas for the code); `FFTECHNO_FONTS` points at a
different font directory. Both the generator and the PNG are tracked; the image is
linked at the top of the README. Regenerate with:

```powershell
.venv\Scripts\python docs\make_cheatsheet.py
```

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
| Amen loop seam | self-correlation at 2 bars | 0.957 at 5.7143 s |
| Delivered trip-hop master | `ebur128` / `ffprobe` | 222.857 s, -13.0 LUFS, -1.2 dBTP |
| Cover video | `ffprobe` | 1920x1080, 30 fps, AAC 320k, 12,984,773 bytes |
| Cheat sheet | Pillow render | 1080x1350 PNG |
| Code audit | AST docstring scan + vulture | 190 functions, 0 missing; no dead code at 60% confidence |
| Lint / format | pyflakes, ruff, black | clean |

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
  below and the voice needs a TTS engine).
- Video: venv with `vapoursynth`, `numpy`, `vs-placebo` (`vspipe`) and a Vulkan GPU.
  Run `.venv\Scripts\python -m vapoursynth config` once (the `Scripts\vapoursynth`
  launcher needs a configured shell).
- Isolation: `onnxruntime` plus the RVM ONNX model (~15 MB) under `tools/rvm/`:

  ```powershell
  .venv\Scripts\pip install onnxruntime
  curl -L -o tools\rvm\rvm_mobilenetv3_fp32.onnx https://github.com/PeterL1n/RobustVideoMatting/releases/download/v1.0.0/rvm_mobilenetv3_fp32.onnx
  ```
- Vocals: a local TTS (offline), chosen with `--tts` or `engine:` in `vocals.md`:
  - **Kitten TTS** (default): `pip install kittenml soundfile huggingface_hub
    phonemizer espeakng_loader` (no torch needed; the nano ONNX model is fetched
    to `tools/kitten/`).
  - **Piper**: unzip the Windows build into `tools/piper/` and put a voice
    (`<name>.onnx` + `.onnx.json`) in `tools/piper/voices/`.
  - **flite**: ffmpeg's own built-in TTS, when the ffmpeg build includes libflite.
    No model files or network; voices `slt`, `kal`, `kal16`, `rms`, `awb`.
- Samples: network access for the first fetch; `yt-dlp` on `PATH` for manifest rows
  whose URL is a YouTube watch/short link (the vinyl row).
- Resource overrides: `FFTECHNO_VSPIPE`, `FFTECHNO_RVM_MODEL`, `FFTECHNO_PIPER`,
  `FFTECHNO_PIPER_VOICES`, `FFTECHNO_KITTEN_MODEL`, `FFTECHNO_KITTEN_CACHE`,
  `FFTECHNO_FONTS`, `FFTECHNO_FONT_SERIF`, `FFTECHNO_FONT_MONO` and
  `FFTECHNO_FONT_MONO_BOLD` point the build at non-default binaries, models or
  fonts.
- Docs: Pillow plus the system Times New Roman / Consolas fonts, only to regenerate
  `docs/ffmpeg_cheatsheet.png`; `FFTECHNO_FONTS` selects a different font directory.
- Dev: `black`, `pyflakes`, `ruff`; `vulture` was used for the one-off dead-code
  audit and is not a runtime dependency.

## 16. Troubleshooting / FAQ

- **Silence or a thin mix?** A stem WAV may be truncated (two builds overlapping).
  Re-run `python -m fftechno audio`; the build lock prevents overlap.
- **"another fftechno build is running"?** A lock file exists; wait, or delete
  `<out>/<song>/logs/.build.lock` if stale.
- **A template error?** `synth` names the missing value.
- **Where are logs?** `<out>/<song>/logs/` (`vspipe.log`, `ffmpeg_video.log`,
  `mix.txt`, plus `vox_*.wav` when a voice is rendered).
- **Which render is current?** The newest `techno*.wav` or
  `techno_visualizer*.mp4`; `swap` and `boost` use an anchored `_latest()` match, so
  a preview file cannot be mistaken for the master.
- **Why is the delivered trip-hop 3:42.9 and the song 3:48.6?** The song is 80 bars
  at 84 BPM (228.571 s); the YouTube cut removes the first two bars (5.714286 s).
- **Where is the cover video?** `output/triphop_samples/ASYNCHRONOUS_1080p.mp4`. It
  is the separate still-art ffmpeg pass in 12.6, not a `video` command render.
- **Why does a build take so long?** Every stem is synthesised at its `sounds.md`
  `sr` (often 192 kHz) for the whole song, with no stem cache; then the mix and the
  two-pass loudnorm read the full length again. Build songs in parallel or use a
  lower `sr` only for a scratch check.
- **How do I make a clean verification build?** `python -m fftechno audio --song S
  --out out2` writes `out2/S/` and leaves `output/` untouched.
- **A YouTube sample fails?** Install `yt-dlp` and check that the URL still has its
  `t=` offset; the fetch length comes from that row's `seconds` column.
- **Noncommercial?** Yes - PolyForm Noncommercial 1.0.0 (`LICENSE.md`). The
  YouTube-sourced vinyl row is not CC-licensed; its URL is in the manifest and it is
  used noncommercially.

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
                             (sax, rhodes, beeps, growl, rim, tom); multiline with
                             blank/# comment lines ignored
templates/README.md          the extended-template format
filters/<name>/*.txt         generated graphs + vox.txt (gitignored; shared across
                             output roots, even with --out)
fftechno/                    config, md, song, looks, effects, proc (build lock),
                             audio, synth, sampler, samples, arrangement, vox, girl,
                             matte, video, cli, visualizer.vpy
samples/                     manifest.md (tracked) + downloaded sets (gitignored):
                             triphop_kit/, breaks/, vinyl/, stoner_kit/
pyproject.toml LICENSE.md README.md SPEC.md TODO.md
docs/AEVAL_TUTORIAL.md       the aevalsrc/aeval guide
docs/SONG_EXPLANATION.md     step-by-step build of triphop_samples
docs/SOUND_DESIGN.md         synthesis techniques used by the templates
docs/ffmpeg_cheatsheet.png   the one-page technique card (linked from README)
docs/make_cheatsheet.py      its generator (Pillow + system fonts, render-only)
output/<name>/               techno*.wav, techno_visualizer*.mp4, girl_loop*.mp4,
                             girl_frames.npy / girl_sprites.npy + girl_pick.npy,
                             lyrics.json, stems/, logs/
output/triphop_samples/      the cover art (cover*.jpg), the delivered
                             ASYNCHRONOUS_1080p*.mp4 and techno_v28/v29.wav
out2/<name>/                 optional clean audio-only audit root (`--out out2`);
                             gitignored, same stems/logs/techno.wav layout
tools/ ascii/                RVM + voice models + the source clip
```

## 19. Risks and limitations

- ffmpeg `eval` has no user variables, so constants repeat inside expressions.
- `loudnorm` runs at 192 kHz internally; the following `aresample=48000` is required.
- `random()` noise is deterministic for a fixed ffmpeg build, but a different build
  may change the noise timbre.
- VapourSynth scripts are Python by definition; the video layer needs the venv.
- The sampler folds every sample to mono. A stereo source (the vinyl loop, the Amen
  break) is summed before placement, so no stereo width survives a sampler stem.
- The YouTube vinyl row is **not** CC-licensed. It is used noncommercially and the
  source URL is recorded; redistributing the sample set separately would need the
  uploader's permission.
- Builds never overwrite, so repeated 4-minute renders accumulate large
  `techno_vN.wav` files and full-length stems. A clean `--out` root or pruning old
  versions is the intended housekeeping.
- Synthesis cost scales with `sr`: a 4-minute stem at 192 kHz is ~46 million samples.
  There is no stem cache, so a full rebuild re-renders every instrument.

## 20. Songs and looks

The code is song-agnostic; song data lives in folders and the style-specific video
code lives in one place.

**Tracks.** `basement` (155 BPM jungle techno, 155 bars, 17 instruments + vox,
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
chain; its source is the first image in `ascii/` unless `video.md` names one. The
image itself is not tracked. `triphop` (84 BPM, 84 bars = 4:00, instrumental, audio only) uses kick,
brk, roll, sub, ep, strings, bell, stab, horn, rise and vinyl. The side-chain key
is kick and the low bus is sub. The master on disk is `output/triphop/techno_v4.wav`.
`triphop_beat` is an 88 BPM, 8-bar scratch (kick, break, bass), not the 4-minute song.
`oldschool_acid` is the oldschool acid techno track: **132 BPM, 132 bars = 4:00**,
A minor, ten synth stems - a 303-style `acid` line, dry synth 909-style kick/clap/hats,
ride/crash/tamb, a low `sub`, a sparse stereo `dubstab` and a dark `pad`. The acid line
uses the `acid_303.txt` variant: a **two-bar, 32-step gated phrase** with rests,
fractional accents, bends, a short attack envelope and a bright/dark filter crossfade.
The sidechain key is `kick` and the low bus is `acid|sub`. Master
`output/oldschool_acid/techno_v3.wav` (240.000 s, -13.0 LUFS / -1.2 dBTP). `warpainting` is the slow psychedelic drone
counterpart, inspired by The Myrrors' "Warpainting" (original composition):
**79 BPM, 158 bars = 8:00**, B minor, thirteen synth stems over an 8-bar
Bm | Gmaj7 | Bm | G loop. Two detuned fuzz guitars drone a B/F# riff with G colour,
with organ, bass, pad, a tom-heavy kit, tambourine and a wah fuzz lead, in a **6.0 s**
convolution reverb. Master `output/warpainting/techno_v2.wav` (480.000 s, -13.0 LUFS /
-1.6 dBTP).
`triphop_samples` is the **sample-based** counterpart: **84 BPM, 80 bars =
228.571 s (3:48.57)**, D minor, four elements. The **Amen break**
(`samples/breaks/amen.wav`) is the only drum source: varispeeded to the 84 BPM grid
with `rate=0.56176` and trimmed to a two-bar loop (5.714286 s). The file's pattern is
really ~149.5 BPM (it repeats every 1.605 s), not the "136" in its name, so the window
now lands on the phrase - verified by self-correlation at the loop point (0.957). It
is high-passed at 200 Hz and low-passed at 8 kHz with a tanh clip so it sits in the
midrange. Over it: `sub_async.txt` (five notes, each **one bar long**, on a **5-bar**
phrase that drifts against the 8-bar harmony, laid back 0.13 s, punchy and low in the
mix; present **only while the piano plays**), and `ep.txt` (dusty FM electric piano,
one chord per bar). The dust is a **real record-groove sample from YouTube**
(`samples/vinyl/crackle.wav`, "Old Vinyl Record Crackle On Loop for 1 Hour", 90 s
from `t=120`, fetched with `yt-dlp` - see the manifest note; not CC-licensed, source
URL recorded, noncommercial use) looped every 31 bars through the sampler **as-is**
apart from a **-1.9 dB gain trim** (`gain=0.8`) - no EQ or compression; the sampler
folds it to mono. One bar (39-40) is a full stop. No second kit. The full render is
`techno_v28.wav` (228.571 s); the delivered cut trims the first two bars to
`techno_v29.wav` (222.857 s, -13.0 LUFS / -1.2 dBTP), and
`ASYNCHRONOUS_1080p.mp4` is 222.857 s. See sections 12.6 and 21.
`psych` is 1960s psychedelic rock with a wall of sound: **110 BPM, 110 bars = 4:00**,
E minor, instrumental. Two detuned fuzz guitars panned wide, a Farfisa-ish organ, a
mellotron pad and tambourine over a rock kit, in a **5.5 s** convolution reverb
(`reverb_seconds`). The fuzz lead deliberately has no phaser or echo: that
combination grew unstable over the full 240 s and was removed.
`stoner` is the heavier, slower counterpart: **76 BPM, 76 bars = 4:00**, D minor /
drop-D, instrumental. A driving 8th-note fuzz riff (D-D-F-G / D-D-F-A) on two
detuned guitars, a thick fuzz bass, big sparse drums, a wah-ish fuzz lead, a low
organ drone in the intro/breakdown, and a **5.0 s** room.
`stoner_samples` is the sample-based version: **80 BPM, 80 bars = 4:00**, C minor /
drop-C. Take 1 used the FreePats pre-distorted guitar, which measured very dark (no
800-2500 Hz growl) and sounded muddy. **Take 2** uses the **clean DI** guitar
(`FSBS-direct`, CC0) pitched naturally, then an **Orange-style fuzz chain** per hit
(pre-EQ -> tanh clip -> mid growl -> cab low-pass), **power chords**
(`chord=1|1.5:0.7|2:0.45`), **sustain** (trim 1.2 s) and a **2-bar riff**
(`pat_bars=2`). Drums are Pearl Master Studio (CC-BY 3.0), bass is FreePats picked
(`electric-bass-YR`, CC0). Guitar zones C2/E2/A2/C3, lead C3/G3, bass C/E2. The growl
band is now ~4 dB below the low-mids (was ~14). Build ~13 s. Drums got a dedicated
pass: **round-robin** snare/tom (3 samples each, `rr`), **ghost notes** and velocity
accents, **humanize** (`jitter`), a groovier kick (1 / 2& / 3 / 4&) and tone shaping
(kick weight + click, snare body + crack, compression) so the kit cuts through the
fuzz.

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
`emits` (`stack` grey frames or `sprites` RGB), an optional `accumulation` hint, and
the `configure` / `decode_filter` / `stack_filter` / `loop_filter` / `sprites` hooks.
Four are registered: `edge`, `pollock`, `outline`, `photo`. Adding a look = one
subclass (and, if it needs knobs, a `| name | key | value |` row in a song's
`video.md`).

`templates/`, `filters/<song>/` (generated, gitignored), `fftechno/visualizer.vpy`
and the models in `tools/` are
shared across every song.

## 21. Sample-based songs - `samples/` + `fftechno/sampler.py`

A song can make its sound from **audio files** instead of `aevalsrc` oscillators. This
section is the whole of the sample support.

**The store.** `samples/manifest.md` (tracked) lists every sample as
`| set | file | url | license | seconds |`. `seconds` is required for YouTube rows
and records the fetch window from the URL's `t=` offset; other rows can leave it
blank. `python -m fftechno samples` downloads the missing
files to `samples/<set>/<file>` and normalises each to a 48 kHz PCM WAV (which also
removes the malformed trailing packet some 24-bit sources carry - the cause of the
benign `Invalid PCM packet` log line). The downloaded files are **not** committed
(`.gitignore` keeps only `manifest.md`); a clone reproduces them from the manifest.
`fftechno/samples.py` holds `fetch`/`prepare`/`run`.

**The instrument.** A `## Samplers` table in `sounds.md` (`| name | sample | params |`)
names a sample and how it plays. `synth.generate` calls
`sampler.graph(song, sample, params)` and writes `filters/<song>/<name>.txt` - the same
node type as a synth stem, so `audio.render_stems` -> mix -> master is unchanged.

A `sample` cell is one path or a `|`-separated map of `path@root` zones
(`gtr_c2.wav@65.41|gtr_f2.wav@87.31|gtr_c3.wav@130.81`). Each hit uses the zone with
the nearest root in semitones, so a wide riff shifts each sample less.

The generated graph reads the file with the `amovie` source filter (a `filter_complex`
source, so no `-i` is needed). A `pat` instrument builds the pattern (`pat_bars`
bars, default one; one branch per hit, placed with `adelay`) and loops it
sample-accurately with `asetpts` -> `atrim=0:bar` -> `apad=whole_len` ->
`aloop=loop=-1:size=<bar frames>` -> `atrim=0:<song.duration>`; the stem is exactly
`song.duration` and the graph stays tiny (a 4-minute pattern is a handful of filters,
not one chain per hit). A `hits` instrument (sparse, absolute) places each hit once
and sums with a silent bed of the full song length. Because `render_stems` passes
**repo-relative** `samples/...` paths to `amovie`, it runs ffmpeg with the repo root
as its working directory (`proc.run(cwd=...)`); otherwise the path would not resolve.
Every sample is resampled to mono (`channel_layouts=mono`), so no sampler stem keeps
stereo width.

Parameters (comma separated `key=value`):

| key | meaning |
|-----|---------|
| `pat` | 16th-step indices inside the pattern (e.g. `0\|6\|10`), looped; spans `pat_bars` bars (default 1) |
| `pat_bars` | number of bars the `pat` pattern spans (default 1) |
| `hits` | absolute 16th steps from the song start (sparse sounds, e.g. a crash every 8 bars) |
| `vel` | per-hit velocity, parallel to `pat`/`hits` |
| `notes` | per-hit frequency (Hz), parallel to `pat`/`hits` |
| `chord` | power-chord ratios per hit, e.g. `1\|1.5:0.7\|2:0.45` (root, fifth at 0.7, octave at 0.45); needs `notes` |
| `rr` | round-robin sample list (`\|`-separated paths); successive hits cycle through them (kills the machine-gun effect on drums). Overrides the map |
| `jitter` | per-hit timing humanize in ms (deterministic, +/- that much) |
| `root` | the recorded frequency for a single path (a map has its own `@root` per zone); each hit is pitched by `note/root` with `asetrate` (varispeed) |
| `trim` | seconds each copy plays (default: the whole file) |
| `rate` | base `asetrate` varispeed factor (applied after the note pitch) |
| `tempo` | `atempo` factor (changes speed, keeps pitch) |
| `fx` | extra per-hit filters, `;`-separated (`;` becomes `,`), e.g. `highpass=f=60;lowpass=f=6000;asoftclip=type=tanh:threshold=0.8` |
| `gain` | per-instrument gain |

Use `pat` **or** `hits`, not both. `pat` is a list of **step indices**, not a
16-value gate string: `pat=0|6|10` hits steps 0, 6 and 10. Every hit is placed by an
**absolute** `adelay` (milliseconds), so there is no cumulative drift. `pat` is
looped with `aloop` after `asetpts` and an exact `whole_len`; the loop boundaries are
sample-accurate (measured). For a looped pattern, each copy is cut at the pattern
boundary (`pat_bars * bar`), so set `trim` at most that length.

Examples (step indices, not gates):

```
| name  | sample                          | params |
|-------|---------------------------------|--------|
| kick  | samples/stoner_kit/kick.wav     | pat=0\|6\|8\|14, trim=0.55 |
| brk   | samples/breaks/amen.wav         | hits=0\|32\|64\|96, rate=0.56176, trim=5.714286 |
| vinyl | samples/vinyl/crackle.wav       | pat=0, pat_bars=31, trim=88.571429, gain=0.8 |
```

`stoner_samples` pitches a sampled guitar and bass (roots C2 = 65.41, C3 = 130.81)
and uses a 2-bar, 16-hit riff:

```
| name | sample                        | params |
|------|-------------------------------|--------|
| bass | samples/stoner_kit/bass.wav   | pat=0\|2\|4\|6\|8\|10\|12\|14\|16\|18\|20\|22\|24\|26\|28\|30, pat_bars=2, notes=65.41\|65.41\|77.78\|87.31\|65.41\|65.41\|77.78\|98\|65.41\|65.41\|77.78\|87.31\|103.83\|103.83\|98\|87.31, trim=0.8 |
| gtr  | samples/stoner_kit/di_c2.wav@65.41\|di_e2.wav@82.41\|di_a2.wav@110\|di_c3.wav@130.81 | pat=0\|2\|4\|6\|8\|10\|12\|14\|16\|18\|20\|22\|24\|26\|28\|30, pat_bars=2, notes=65.41\|65.41\|77.78\|87.31\|65.41\|65.41\|77.78\|98\|65.41\|65.41\|77.78\|87.31\|103.83\|103.83\|98\|87.31, chord=1\|1.5:0.7\|2:0.45, trim=1.2 |
```

## 22. Deliverables and audit

**Tracked documentation.** `README.md` is the practical guide (setup, commands,
editing, samples, video, troubleshooting). `SPEC.md` is this SRS.
`docs/AEVAL_TUTORIAL.md` is the from-scratch `aevalsrc`/`aeval` guide.
`docs/SONG_EXPLANATION.md` walks through the `triphop_samples` build with the render
command first, then a songwriting approach. `docs/SOUND_DESIGN.md` describes the
synthesis techniques used by the templates. `TODO.md` is the open-work list only;
the design history lives in section 23. `docs/ffmpeg_cheatsheet.png` and its
generator are tracked because the card is embedded in the README.

**Rendered deliverables.** `output/` is gitignored. The current trip-hop assets are
`output/triphop_samples/techno_v28.wav` (full 228.571 s render),
`output/triphop_samples/techno_v29.wav` (delivered 222.857 s cut),
`output/triphop_samples/ASYNCHRONOUS_1080p.mp4` (the YouTube cut), and
`output/triphop_samples/cover.jpg` plus its clean source `cover_v1.jpg`. Versioned
earlier cuts are kept beside the current one.

**Clean audit builds.** `python -m fftechno audio --song S --out out2` writes an
independent tree under `out2/S/` (gitignored). `filters/S/` is generated and
gitignored, and remains shared across output roots. This is
the recommended way to verify every song without adding `_vN` files to `output/`.
Current status: `basement` (240.000 s) and `triphop_beat` (21.818 s) completed an
`out2` run; `hardgroove` was partial and the remaining songs were skipped. The full
song run is the first open item in `TODO.md`.

**Code audit (this pass).**

- Every Python function and method has a docstring: 190 functions, 0 missing
  (AST scan over `fftechno/*.py`, `fftechno/visualizer.vpy` and `docs/make_cheatsheet.py`).
- `pyflakes`, `ruff` and `black --check` are clean; `vulture` reports no dead code
  at 60% confidence.
- Removed stale code: the unused `Look.decode` attribute (the pipeline uses
  `decode_filter`) and the unused `ascii_for_block` cache helper in the visualizer.
- Fixed the stale `--tts` error message (it now lists `flite`) and the stale
  `pyproject.toml` / package descriptions.
- Removed the remaining hardcoded couplings: video FPS is passed through
  `FFTECHNO_FPS` into both the visualizer and the shader; the package version is
  dynamic from `fftechno.__version__` (0.3.0, with `pyproject.toml` reading it and
  `[tool.setuptools] packages = ["fftechno"]` scoping wheel builds); YouTube fetch
  length comes from the manifest `seconds` column; voice treatment, master
  EQ/limiter, video encode settings, square `roles`/`order` and look thresholds are
  configurable rather than fixed in code. VapourSynth, RVM, Piper, Kitten and the
  cheat-sheet fonts also have `FFTECHNO_*` path overrides; the `photo` look resolves
  its source from `video.source` or the first image in `ascii/`.
- The only known repository-level leftover is the separate
  `.worktrees/aeval` git worktree (branch `aeval-split`), which is not part of the
  main build.

## 23. Design history and rejected directions

The current files are the result of a few deliberate reversals. These notes preserve
the durable reasoning behind the current design.

- **Origin.** v0.1 was the hardgroove track (140 BPM) with an ASCII VapourSynth video
  and an espeak-ng voice. v0.2 made songs folders, added `basement` and the
  `outline`/`edge`/`pollock` looks; the later tracks are additional folders.

- **Lossless port.** The hardgroove track was moved from hand-authored ffmpeg graphs
  into markdown; substituting the recorded values reproduces the originals (verified
  at <= -213 dB).
- **Songs are folders.** The early per-song `Song` subclasses and the registry were
  removed; `Song(name)` reads `songs/<name>/`. `fftechno/md.py` is the single
  table/scalar reader for all four control files.
- **Video became a pipeline.** The hard-coded shader was split into a `Look` source
  plus an ordered `Effect` chain; the old shader is the built-in default chain, so a
  song with no `effects:` renders unchanged. `photo` and `squares` later gained
  framing, focus, shift, explicit half-sizes, rings and on/off presence.
- **Stem tails are cut.** `audio.render_stems` cuts every stem at `song.duration`; an
  effect tail (the blow's ping-pong delay) must not stretch the master. `Pan: keep`
  passes an already-stereo stem through instead of folding it to a point. `Levels`
  stems honour the `Pan` table too.
- **`minimal`.** The dry 4-on-4 kick never drops; the random golden-ratio hat was
  replaced by `hat_step`, and `ohat_dyn` varies decay and velocity per hit. The single
  `blow` is a panned, arranged stem with a built-in ping-pong delay. The final
  `Sections` row is exactly `fade_bars` long so the track does not end in silence.
- **`psych`.** The 5.5 s convolution IR supplies the wall of sound. The fuzz lead's
  phaser/echo combination grew unstable over 240 s and was removed. The stoner
  guitars later exposed `aecho`'s `in_gain x out_gain` attenuation; they use a
  transparent echo instead.
- **`stoner_samples`.** Take 1's pre-distorted guitar was too dark; take 2 uses the
  clean DI plus a per-hit fuzz chain, power chords, sustain and a 2-bar riff. The
  sampler gained `rr`, `jitter`, `chord`, `pat_bars` and multi-sample maps; `pat` is a
  list of step indices, not a gate pattern.
- **`triphop_samples`.** The Amen's real period is ~149.5 BPM, not the "136" in its
  filename; `rate=0.56176` makes the two-bar window land on the phrase. The sub is
  bar-length and asynchronous; the vinyl is a real YouTube groove used as-is with a
  -1.9 dB trim. The delivered cut removes two bars. Synthetic and CC0 vinyl
  candidates, the Freesound bed and the sparse "silent groove" were rejected.
- **Tooling.** ffmpeg 9 uses `-/filter_complex FILE`; outputs are versioned and never
  overwritten; the build lock is exclusive; `--safe` is opt-in; `--out` keeps audit
  builds out of `output/`.
