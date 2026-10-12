# SPEC.md - fftechno (SRS)

Technical specification of **fftechno**: a four-minute underground techno track
(currently a 155 BPM "Basement"-style jungle-techno tune; an earlier hardgroove
track is in git history) plus a black-and-white dancing-girl music video. Every
sound is synthesized by **ffmpeg** (the voice by a local neural TTS); the build
tooling is Python. The arrangement and every instrument parameter live in
markdown.

---

## 1. Purpose and scope

Produce a fixed-length techno track and a video, driven by a song's markdown files, using
`ffmpeg` for sound. The original hardgroove port to markdown was **lossless**
(substituting the recorded parameter values reproduces the original ffmpeg filter
graphs, verified by rendering comparison).

The video's main visual is a black-and-white dancing girl, drawn as a white
**silhouette outline** with the **blue hair chroma-keyed** from the source and cut
to random stills on the beat (the `outline` look). Two other looks share the same
pipeline: `edge` (an RVM-matted white line drawing) and `pollock` (an all-over
abstract painting from whole-frame edges). The voice is synthesised with a local
neural TTS - **Kitten TTS** (`kittenml`) by default, or **Piper** - both offline.

In scope: `aevalsrc`-based synthesis, drum/gate patterns, mix automation, side-chain,
convolution reverb, two-pass loudness mastering, an RVM / `edgedetect` / silhouette
video with on-screen lyrics, and a reproducible build.

Out of scope: real-time performance, a GUI, MIDI import, sample playback.

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
              songs/<song>/video.md -> Look -> beat-synced data
                           v
              output/<song>/girl_loop.mp4
              + girl_frames.npy  /  girl_sprites.npy + girl_pick.npy
                           v
              vspipe visualizer.vpy -> ffmpeg -> output/<song>/techno_visualizer.mp4
```

## 5. Build pipeline

Commands (`python -m fftechno ...`):

Commander: every command takes `--song <name>` (default `basement`).

| Command | Phases |
|---------|--------|
| `synth --song S` | `songs/S/sounds.md` + `templates/` -> `filters/S/<name>.txt` |
| `audio --song S [--safe] [--tts kitten\|piper]` | `synth` -> IR -> vocals -> stems -> mix -> master -> `output/S/techno.wav` |
| `girl --song S [--look edge\|pollock\|outline] [--mode reset\|trail\|build]` | source clip -> look -> `output/S/girl_loop.mp4` + picture data |
| `video --song S [--look ..] [--mode ..] [--boost F] [--static]` | `girl` -> render -> mux -> 720p preview -> optional re-level |
| `all --song S [--look ..] [--mode ..] [--safe] [--tts ..] [--boost F] [--static]` | `audio`, then `girl`, then `video` |
| `boost F --song S` | re-encode the MP4 audio at gain `F` (video copied) |

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

Tables (all required unless noted):

- **Stems** - `| stem |`; the mix input order (one `-i` per row). Defines which
  stems exist.
- **Boosts** - `| stem | boost |`; a per-stem gain multiplied over the section gains.
- **Sections** - `| bars | <stem> | ... |`; rows are bar ranges (`start-end`),
  columns are arranged stems, cells are gains. The last section fades.
- **Pan** - `| stem | mode | left | right |`; `mode` is `center`, `haas`, or
  `stereo` (with `left`/`right` gains).
- **Effects** - `| effect | value |`; `reverb_send`, `reverb_hpf`, `reverb_wet`,
  `sidechain_threshold/ratio/attack/release`, `stereo_width`,
  `bus_threshold/ratio/attack/release`.
- **Levels** - `| stem | level |`; fixed level for non-arranged stems (vox).

Rules: section ranges are contiguous; the last row's end equals `bars`; every stem
has a `Pan` row; `low_bus` stems must be in `Stems`. Missing entries raise.

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
- Globals provided: `sr, dur, lp, osr, bar, step, beat, gold, vbase, vamt, grid,
  halfgrid, beatgrid`.

## 8. Instruments

Seventeen instruments, all parameterised (values in `sounds.md`):

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

The **vox** stem is not a template: `fftechno/vox.py` synthesizes short phrases
with a local neural TTS (Kitten TTS via `kittenml`, or Piper) and places them via
`filters/<song>/vox.txt`; the same `songs/<song>/vocals.md` times are written to
`output/<song>/lyrics.json` for the on-screen lyrics.

**Losslessness.** The generated graphs reproduce the original hand-authored
expressions value-for-value (verified: rendering each stem against its original
differs only by float rounding, <= -213 dB).

## 9. Mix specification - `fftechno/arrangement.py`

`build_graph(song)` emits, in `Stems` order:

- per arranged stem: `[i]volume=volume='<boost>*<nested if(lt(t,..))>':eval=frame[stemv]`
  followed by a `pan=stereo|...` to `[stem]`; the final section fades over
  `fade_bars`;
- per `Levels` stem: `[i]volume=<level>,pan=stereo|c0=0.5*c0|c1=0.5*c0[stem]`;
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

`output/<song>/techno.wav`: pcm_s16le, 48 kHz, 2 channels, 240.000 s, -13.0 LUFS,
true peak -1.0 dBFS.

## 12. Video - `visualizer.vpy`

VapourSynth + vs-placebo. The main visual is the dancing girl: a small piece of
per-frame data is written into a low-res YUV444P16 clip (960x540), the audio data
strip (64 bands + bass + kick + energy) into the top rows, and the clip is
upscaled to 1920x1080. A GLSL shader reads the picture (`HOOKED_tex`), the strip
and `frame` (time) and applies a kick-synced brightness punch plus a light
vignette/grain (no overlay); it **preserves chroma** (so the blue hair stays blue)
and masks the top strip rows black. Output is YUV420P8, piped to ffmpeg by `vspipe -c y4m`.
`--static` renders a single frozen frame.

Environment inputs: `FFTECHNO_AUDIO` (the mastered WAV), `FFTECHNO_GIRL_FRAMES`
(grey frame stack - edge/pollock), `FFTECHNO_GIRL_SPRITES` + `FFTECHNO_GIRL_PICK`
(RGB sprites + per-frame index - outline), `FFTECHNO_POLLOCK` (paint-accumulation
mode) and `FFTECHNO_STATIC`. If none is present it falls back to ASCII art of any
`ascii/*.jpg|png`.

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

- **Tempo/length:** edit `bpm`/`bars` and the `Sections` rows.
- **New instrument:** add a `templates/<name>.txt` (with `{{keys}}`), a row in
  `sounds.md`, the name in the `Stems` table, a `Pan` row, a `Boosts` row, and a
  `Sections` column.
- **New step melody:** use `{{if_steps(seq; grid; default)}}` and a `\|` list.
- **Mix effects:** the `Effects` table.
- **Video:** edit `SHADER` in `visualizer.vpy`.

## 18. File inventory

```
songs/<name>/                control surfaces: song.md, sounds.md, vocals.md, video.md
templates/*.txt              synth schematics (16 used by 17 instruments; some legacy ones remain)
filters/<name>/*.txt         generated graphs + vox.txt
fftechno/                    config, song, looks, proc (build lock), audio, synth,
                             arrangement, vox, girl, matte, video, cli
visualizer.vpy               the video
pyproject.toml LICENSE.md README.md SPEC.md TODO.md CHANGELOG.md
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

**Songs** (`fftechno/song.py`). An abstract `Song` exposes a track: paths to its
four markdown files; its `filters`/`output`/`stems`/`logs` dirs; its parsed
arrangement; derived `bpm`/`bar`/`duration`; its `vocals()` (TTS engine/voice +
phrase times) and `video()` (source, crop, look, loop) settings; and per-song
output paths (`techno.wav`, `techno_visualizer*.mp4`, `girl_*`, `lyrics.json`).
Concrete songs are thin subclasses (`Basement`, `Hardgroove`) registered in a
`SONGS` dict; a folder with no subclass still works (a generic `Song`). Adding a
track = add `songs/<name>/` with the four markdown files (plus, optionally, a
subclass).

**Looks** (`fftechno/looks.py`). `girl.py` is a generic pipeline (decode ->
optional matte -> look -> fit -> emit); a `Look` strategy declares `needs_matte`,
`emits` (`stack` grey frames or `sprites` RGB), an optional `accumulation` hint and
`decode` (`native`/`fitted`), plus `stack_filter(w,h)` (a `-filter_complex` body)
and/or `sprites(frames, model)`. Three are registered: `edge`, `pollock`,
`outline`. Adding a look = one subclass (and, if it needs knobs, a
`| look | key | value |` row in a song's `video.md`).

`templates/`, `filters/<song>/`, `visualizer.vpy` and the models in `tools/` are
shared across every song.
