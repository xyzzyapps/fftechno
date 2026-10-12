# SPEC.md - fftechno (SRS)

Technical specification of **fftechno**: a four-minute hardgroove techno track plus
a black-and-white dancing-girl music video. Every sound is synthesized by **ffmpeg**; the
build tooling is pure Python. The arrangement and every instrument parameter live
in markdown, and the build is reproducible.

---

## 1. Purpose and scope

Produce a fixed-length techno track and a video, driven by two markdown files, using
only `ffmpeg` for sound. Porting the original hand-authored track to markdown must
be **lossless**: substituting the recorded parameter values into the templates must
reproduce the original ffmpeg filter graphs (verified by rendering comparison).

The video's main visual is a **black-and-white, edge-detected dancing girl**, cut
out of the source clip with Robust Video Matting (RVM, ONNX), edge-detected, and
looped on the beat grid. The voice stem is synthesised with ffmpeg's built-in
`flite` filter (no external TTS).

In scope: `aevalsrc`-based synthesis, drum/gate patterns, mix automation, side-chain,
convolution reverb, two-pass loudness mastering, an RVM + `edgedetect` video, and a
reproducible build.

Out of scope: real-time performance, a GUI, MIDI import, sample playback.

## 2. Glossary

- **Stem** - one layer of the mix (kick, bass, ...). Rendered to `output/stems/`.
- **Template** - an ffmpeg filtergraph with `{{key}}` placeholders (`templates/`).
- **Instrument** - a row in `sounds.md`: a template plus the values for it.
- **Grid / step** - a 16th note. A bar is 16 steps.
- **Gate** - a per-step on/off (0/1) value; drum `gates` lists are 16 values.
- **LUFS / true peak** - loudness / peak measures used for mastering.

## 3. Global constants

| Name | Value |
|------|-------|
| BPM | 140 |
| bars | 140 (4:00) |
| sample rate | 48000 Hz (oscillators generated at 192000 Hz, then downsampled) |
| loudness target | -13 LUFS, true peak -1.0 dBFS |
| stems | kick, clap, hat, ohat, conga, bongo, rim, shaker, bass, acid, growl, beeps, vox |

Derived: `beat = 60/140 = 0.428571 s`, `step (16th) = 0.107143 s`,
`bar = 1.714286 s`.

## 4. Architecture and data flow

```
  song.md  (arrangement + mix)          sounds.md + templates/  (instruments)
      |                                        |
      |  arrangement.py                        |  synth.py
      v                                        v
  mix filtergraph  (output/logs/mix.txt)   filters/<name>.txt   (12 graphs)
      |                                        |
      |                                        |  audio.render_stems()
      |                                        v
      |                                   output/stems/<name>.wav   (+ vox.wav)
      |                                        |
      +--------------------+-------------------+
                           v
              mix  ->  output/mix_pre.wav
                           v
              master (2-pass loudnorm)  ->  output/techno.wav
                           v
              ascii/*.mp4 -> RVM matte -> edgedetect -> beat-locked loop
                           v
              output/girl_loop.mp4  +  output/girl_frames.npy
                           v
              vspipe visualizer.vpy  ->  ffmpeg  ->  output/techno_visualizer.mp4
```

## 5. Build pipeline

Commands (`python -m fftechno ...`):

| Command | Phases |
|---------|--------|
| `synth` | `sounds.md` + `templates/` -> `filters/<name>.txt` |
| `audio` | `synth` -> IR -> vocals -> stems -> mix -> master -> `techno.wav` |
| `girl` | source clip -> RVM matte -> edge -> `girl_loop.mp4` + `girl_frames.npy` |
| `video [--boost F] [--static]` | `girl` -> render -> mux -> 720p preview -> optional re-level |
| `all [--boost F] [--static]` | `audio`, then `girl`, then `video` |
| `boost F` | re-encode the MP4 audio at gain `F` (video copied) |

Filtergraphs are read from files with the ffmpeg 9 syntax `-/filter_complex FILE`
(the old `-filter_complex_script` was removed).

Outputs are written with `config.unique_path`: if the target exists, the build
writes `name_v2.ext`, `_v3`, ... so existing renders are never overwritten.

A **build lock** (`output/logs/.build.lock`, created with `O_EXCL`) prevents two
builds writing the same outputs concurrently; a second run exits with a clear
message.

## 6. Control surface A - `song.md`

Scalars (all required):

```
bpm: 140
bars: 140
fade_bars: 7            # the final section fades to silence over this many bars
sidechain_key: kick     # which stem drives the ducking
low_bus: bass|growl     # stems grouped and ducked under the key
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
- **Levels** - `| stem | level |`; fixed level for non-arranged stems (vox, beeps).

Rules: section ranges are contiguous; the last row's end equals `bars`; every stem
has a `Pan` row; `low_bus` stems must be in `Stems`. Missing entries raise.

## 7. Control surface B - `sounds.md` + `templates/`

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
- Globals provided: `sr, dur, lp, osr, bar, step, gold, vbase, vamt, grid,
  halfgrid, note_grid`.

## 8. Instruments

Twelve instruments, all parameterised (values in `sounds.md`):

| Instrument | Template | Highlights |
|------------|----------|------------|
| kick | kick.txt | `beat, f0, sweep, rate, decay, click_*, sub_*, noise_*, eq_*, clip` |
| clap | clap.txt | `beat, decay1/2, tone_*, hp, lpc` (beat-gated) |
| hat | hat.txt | `decay, hp` + velocity (`vbase/vamt/gold`) |
| ohat | ohat.txt | offbeat (`off, beat, win`), `decay, hp` |
| conga | conga.txt | tuned drum: `pitches` (16-step), `gates` (16-step), `sweep, rate, decay, hp, lpc, aecho`, plus a `slap` transient |
| bongo | tom.txt | `pitches` (16-step), `gates` (16-step), `sweep, rate, decay, hp, lpc, aecho` |
| rim | rim.txt | `tone_f, n_amt, decay, gates, hp` |
| shaker | shaker.txt | `decay, gates, hp` |
| bass | bass.txt | `notes` (16-step), `detune, decay1/2, lp_bass, eq_*, asubboost, clip` |
| acid | acid.txt | `notes, gates, bends` (16-step), filter crossfade + resonant 24 dB/oct |
| growl | growl.txt | grain train + FM carrier + `phrase, gates` (8-step half-bar) |
| beeps | beeps.txt | `notes, notelen, ratio, decay, adelay` placements |

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

The graph is written to `output/logs/mix.txt`.

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

## 11. Output format

`output/techno.wav`: pcm_s16le, 48 kHz, 2 channels, 240.055 s, -13.0 LUFS,
true peak -1.0 dBFS.

## 12. Video - `visualizer.vpy`

VapourSynth + vs-placebo. The main visual is the edge-detected dancing girl: a
compact uint8 frame stack (`output/girl_frames.npy`, 960x540, one loop = a whole
number of beats) is written into the luma plane of a low-res YUV444P16 clip, the
audio data strip (64 bands + bass + kick + energy) into the top rows, and the clip
is upscaled to 1920x1080. A GLSL shader reads the girl (`HOOKED_tex`), the strip
and `frame` (time) and draws a subtle black-and-white Berlin overlay plus a
kick-synced brightness punch; the top strip rows are masked black. Output is
YUV420P8, piped to ffmpeg by `vspipe -c y4m`. `--static` renders a single frozen
frame.

The visualizer reads its inputs from the environment: `FFTECHNO_AUDIO` (the
mastered WAV), `FFTECHNO_GIRL_FRAMES` (the frame stack) and `FFTECHNO_STATIC`. If
the frame stack is missing it falls back to the original ASCII art of any
`ascii/*.jpg|png`.

### 12.1 Girl pipeline - `fftechno/girl.py` + `fftechno/matte.py`

1. `source_clip()`: the first video in `ascii/`.
2. Decode `GIRL_CROP_START .. +GIRL_CROP_DURATION` (2.0 s..5.0 s = 7 beats) at
   native size/fps.
3. `RVMMatte` (RVM mobilenetv3 ONNX via `onnxruntime`, recurrent so temporally
   stable) -> per-frame alpha; `largest_component` keeps only the subject (drops
   the crowd); composite over black.
4. ffmpeg: `fps=30`, fit to 16:9 with black bars (`scale`+`pad`), `edgedetect`
   (white lines on black).
5. Emit `output/girl_loop.mp4` (1920x1080, 3.0 s, silent, versioned) and
   `output/girl_frames.npy`.

Because 3.0 s = 7 beats = 1/80 of the 4:00 track, the loop tiles the whole video
exactly `80` times and always restarts on a beat.

## 13. Verification and acceptance

| Check | Method | Result |
|-------|--------|--------|
| Template losslessness | render each stem vs its original, compare | <= -213 dB (float noise) |
| Filter graphs valid | `ffmpeg -/filter_complex` per stem | clean |
| Loudness | `ebur128` | -13.0 LUFS |
| True peak | `ebur128=peak=true` | -1.0 dBFS |
| Whole track | `techno.wav` vs reference build | byte-identical (SHA256 match) |
| Reproducible | rebuild, compare | identical |

## 14. Reproducibility

`python -m fftechno audio` regenerates `filters/*.txt`, the stems, the mix and the
master from markdown alone. The reference track reproduces **byte-for-byte**; the
build lock guarantees a single writer.

## 15. Requirements and environment

- **ffmpeg 9+ / ffprobe** (gyan.dev full build). Audio filters: `aevalsrc`,
  `asubboost`, `asoftclip`, `acrusher`, `equalizer`, `highpass`, `lowpass`, `asplit`,
  `amix`, `pan`, `haas`, `extrastereo`, `sidechaincompress`, `acompressor`,
  `alimiter`, `loudnorm`, `afir`, `aresample`, `aformat`, `adelay`, `apad`, `volume`
  (`eval=frame`), `flite`. Video filters: `edgedetect`, `format`, `fps`, `scale`,
  `pad`. Filtergraphs are read from files with `-/filter_complex FILE`
  (`-filter_complex_script` was removed in ffmpeg 8/9).
- Python 3.10+ (the audio tooling uses only the standard library).
- Video: venv with `vapoursynth`, `numpy`, `vs-placebo` (`vspipe`) and a Vulkan GPU.
  Run `.venv\Scripts\python -m vapoursynth config` once (the `Scripts\vapoursynth`
  launcher needs a configured shell).
- Isolation: `onnxruntime` plus the RVM ONNX model (~15 MB) under `tools/rvm/`:

  ```powershell
  .venv\Scripts\pip install onnxruntime
  curl -L -o tools\rvm\rvm_mobilenetv3_fp32.onnx https://github.com/PeterL1n/RobustVideoMatting/releases/download/v1.0.0/rvm_mobilenetv3_fp32.onnx
  ```
- Vocals: ffmpeg's built-in `flite` filter (voice `slt`); no external TTS binary.

## 16. Troubleshooting / FAQ

- **Silence or a thin mix?** A stem WAV may be truncated (two builds overlapping).
  Re-run `python -m fftechno audio`; the build lock prevents overlap.
- **"another fftechno build is running"?** A lock file exists; wait, or delete
  `output/logs/.build.lock` if stale.
- **A template error?** `synth` names the missing value.
- **Where are logs?** `output/logs/` (`vspipe.log`, `ffmpeg_video.log`,
  `mix.txt`).
- **Noncommercial?** Yes - PolyForm Noncommercial 1.0.0 (`LICENSE.md`).

## 17. Extension guide

- **Tempo/length:** edit `bpm`/`bars` and the `Sections` rows.
- **New instrument:** add a `templates/<name>.txt` (with `{{keys}}`), a row in
  `sounds.md`, the name in the `Stems` table, a `Pan` row, a `Boosts` row, and a
  `Sections` column.
- **New step melody:** use `{{if_steps(seq; grid; default)}}` and a `\|` list.
- **Mix effects:** the `Effects` table.
- **Video:** edit `SHADER`, grid or palette in `visualizer.vpy`.

## 18. File inventory

```
song.md sounds.md            control surfaces
templates/*.txt              synth schematics (12 templates incl. conga)
filters/*.txt                generated graphs + vox.txt
fftechno/                    config, proc (build lock), audio, synth,
                             arrangement, vox, girl, matte, video, cli
visualizer.vpy               the video
pyproject.toml LICENSE.md README.md SPEC.md TODO.md
output/                      techno*.wav, techno_visualizer*.mp4,
                             girl_loop*.mp4, girl_frames.npy, stems/, logs/
tools/ ascii/                RVM model + the source clip
```

## 19. Risks and limitations

- ffmpeg `eval` has no user variables, so constants repeat inside expressions.
- `loudnorm` runs at 192 kHz internally; the following `aresample=48000` is required.
- `random()` noise is deterministic for a fixed ffmpeg build, but a different build
  may change the noise timbre.
- VapourSynth scripts are Python by definition; the video layer needs the venv.
