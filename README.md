# fftechno

[![Built with DeepSeek](https://img.shields.io/badge/Built%20with-DeepSeek-4D6BFE?logo=deepseek&logoColor=white)](https://www.deepseek.com/)

A **four-minute hardgroove techno track** - granular robotic-speech voice, a 303
acid line, and spoken female vocals - synthesized **entirely by ffmpeg** (no DAW,
no sampler), plus a **black-and-white VapourSynth + GLSL** visual that turns images
into **ASCII art** with Berlin-techno overlays, muxed into a final video.

The build tooling is **pure Python** (`fftechno/`); ffmpeg does all the sound.

Outputs:
- `output/techno.wav` - 48 kHz stereo, 4:00, -13.0 LUFS
- `output/techno_visualizer.mp4` - 1920x1080 30 fps, ASCII + B/W shader
- `output/techno_visualizer_720p.mp4` - web preview

## The track

A **4:00 hardgroove / loop-techno track at 140 BPM** (140 bars, 4/4), built from
13 synthesized parts. Everything is generated from scratch with ffmpeg `aevalsrc`
expressions and filter graphs - no samples, no VSTs. Mood: dark, driving,
warehouse-oriented, with an acid lead, a robotic voice and a small amount of
found-object charm (Windows-startup bells, TTS vocal hooks).

### Groove and drums

- **Kick** - a 4-on-the-floor 909-style sine whose pitch sweeps ~268 -> 48 Hz with
  a fast decay, plus a 1.2 kHz click, a 45 Hz sub-octave and a short noise
  transient. It is the loudest element and keys the side-chain.
- **Clap** - filtered noise burst + a 200 Hz body on beats 2 and 4 (the backbeat).
- **Closed hat** - high-passed noise on every 16th, with per-step velocity so it
  swings instead of machine-gunning.
- **Open hat (offbeat)** - a longer high-passed noise hit on the "&" of each beat
  (the classic off-beat open hat that defines the bounce).
- **Toms** - syncopated pitched toms/congas (steps 0,1,3,5,6,8,9,11,13,14 of the
  bar) with a pitch drop, for the tribal hardgroove roll.
- **Bongo** - a higher tribal layer (steps 2,4,7,10,12,15) that fills the gaps.
- **Rim** - a very short click (noise + 1.5 kHz tone) on the off-beat 8ths
  (steps 1,5,9,13) for definition.
- **Shaker** - a fast high-passed noise tick on the off-beat 16ths.

All percussion carries a golden-angle per-step velocity so nothing sits perfectly
on the grid.

### Low end

- **Bass** - a rolling 16th-note saw line alternating between A (55 Hz) and G
  (49 Hz), an octave jump for the turnarounds, with a sub-octave sine and a
  slightly detuned unison layer for weight and width. A 45 Hz shelf and an
  `asubboost` push the deep end. It is heavily side-chained to the kick so the
  kick always cuts through.

### 303 acid

- **Acid** - a Roland-303-style monosynth line: a saw oscillator running a 16-step
  pattern (A, C, E, G, F, D ...) with accented steps, rests, and per-note
  pitch-bend "squawk". Its filter is two layers: a bright/dark crossfade
  (bright saw vs. dark low-passed) whose cutoff sweeps on a fast per-note LFO and a
  slow 16-second LFO, plus a **real resonant 24 dB/oct low-pass** (two cascaded
  biquads) for the squelch. It runs into tanh saturation and a light bit-crush.

### Voices

- **Robotic speech (growl)** - a formant-FM carrier multiplied by a granular
  *grain train* (overlapping Hann grains) and a per-slot syllable window, with an
  8-slot pitch contour. It reads as a stuttering machine voice rather than a bass
  growl, and moves between the low and mid range.
- **Vocal hooks** - nine female phrases down-pitched from espeak-ng ("speak to me",
  "come on", "feel it", "hard groove", "let go", "trust me", "lock in",
  "take me higher", "hands up"), each placed three times across the track with a
  reverb send.
- **Beeps** - a Win-startup-style bell arpeggio (C5 E5 G5 C6 E6, two partials
  including an inharmonic 2.76x for the metallic "boop"), fired at 0:00.5, 1:08
  and 2:17.

### Arrangement

The arrangement is per-stem gain automation **generated from `song.md`** (the
volume follows time with `eval=frame`). Seven regions:

| Bars | Time | Section | Notes |
|------|------|---------|-------|
| 0-8 | 0:00-0:14 | **Intro** | kick + hat + acid + beeps; no bass/clap/perc |
| 8-32 | 0:14-0:55 | **Main 1** | full kit, bass and growl enter |
| 32-40 | 0:55-1:09 | **Break 1** | kick and clap drop out; growl lifted |
| 40-72 | 1:09-2:03 | **Main 2** | full |
| 72-80 | 2:03-2:17 | **Break 2** | kick and clap drop out |
| 80-133 | 2:17-3:48 | **Main 3** | full, growl and acid pushed |
| 133-140 | 3:48-4:00 | **Outro** | 12-second fade to silence |

### Production

- **Anti-aliasing** - oscillators are generated at 192 kHz, low-passed at 19 kHz
  and downsampled, so the saws don't alias.
- **Space** - a convolution reverb built from a synthesized decaying-noise impulse
  response (`afir`) on a high-passed send bus (kick and bass stay dry and centred).
- **Stereo** - per-stem panning (hat left, ohat/rim right, etc.), a Haas widener
  on the perc, and generous `extrastereo` on the bus; mid sits ~4 dB above side.
- **Master** - two-pass linear loudness to **-13 LUFS** with a true-peak limiter
  and dither. The final MP4 is re-leveled to ~**-8.9 LUFS** (the `boost` step) for
  club/phone playback.

### Visual (B/W ASCII)

A 1920x1080 30 fps VapourSynth + GLSL video: every image in `ascii/` is turned into
**ASCII art** (a numpy bitmap font) and shown once through a shuffled playlist (each
image at least 3 times), with a **black-and-white** Berlin overlay - hypnotic rings,
audio-reactive spokes, a grid, scanlines, kick glitches and grain - driven by the
audio's spectrum, bass, kick and energy.

## Requirements

- `ffmpeg` / `ffprobe` on `PATH` (gyan.dev full build).
- Python 3.10+ (the tooling is standard library only).
- For the video: a venv with `vapoursynth`, `numpy`, `vs-placebo` (provides `vspipe`).
- For the vocals: **espeak-ng** under `tools/`.

## Setup (one-off)

```powershell
python -m venv .venv
.venv\Scripts\pip install vapoursynth numpy vs-placebo
.venv\Scripts\vapoursynth config        # registers Python paths for vspipe

# espeak-ng (vocals), no system install:
curl -L -o tools/espeak-ng.msi https://github.com/espeak-ng/espeak-ng/releases/download/1.52.0/espeak-ng.msi
msiexec /a tools\espeak-ng.msi /qn TARGETDIR="%CD%\tools\espeak-ng"
```

## Build

```powershell
python -m fftechno audio          # stems -> mix -> master  -> output/techno.wav
python -m fftechno video          # render + mux the ASCII video
python -m fftechno all            # audio, then video
python -m fftechno boost 2.0      # re-level the finished MP4s (video copied)
```

`audio` also regenerates the reverb IR and the espeak vocal stem. Put images
(jpg/png) in `ascii/`; every image is used at least 3 times in the video.

## Sequencing music - a new-user guide

You sequence the track by editing markdown, then running two commands. No DAW, no
piano-roll, no samples - the notes are `aevalsrc` math and the arrangement is a
table of gains over time.

### The control files

| file | what it controls |
|------|------------------|
| `song.md` | tempo, length, **when** each stem plays (section gains), panning, and the global mix effects |
| `sounds.md` | **what** an instrument sounds like (optional; the shipped kit lives in `filters/`) |

Everything else is generated, or is a raw ffmpeg graph you never need to touch.

### The 30-second loop

```powershell
# 1. edit song.md (and optionally sounds.md)
# 2. rebuild the audio
python -m fftechno audio
# 3. listen
ffplay output/techno.wav
```

Repeat until it sounds right. When happy, render the video with
`python -m fftechno video` (add `--boost 2.0` to re-level it hot).

### `song.md`, part by part

**1. Header scalars**

```markdown
bpm: 140        # tempo; one bar = 4 beats = 4 * 60/bpm seconds
bars: 140       # total length (4:00 at 140 BPM)
fade_bars: 7    # the final section fades to silence over this many bars
```

**2. Boosts** - a fixed gain per stem, multiplied on top of the section gains.
Use it to balance the kit (a kick usually needs to be much louder than a hat).

```markdown
| stem | boost |
|------|-------|
| kick | 2.55  |
| hat  | 2.55  |
| bass | 1.15  |
```

**3. Sections** - the arrangement itself. One row per time region; the first column
is the bar range, every other column is a stem (the columns are the stems you are
sequencing, from `MIX_INPUTS` in `fftechno/config.py`).

```markdown
| bars    | kick | clap | hat  | ohat | perc | ... | acid |
|---------|------|------|------|------|------|-----|------|
| 0-8     | 0.90 | 0.00 | 0.50 | 0.00 | 0.00 | ... | 0.80 |
| 8-32    | 1.00 | 0.70 | 0.55 | 0.50 | 0.70 | ... | 0.90 |
| 32-40   | 0.00 | 0.00 | 0.40 | 0.25 | 0.50 | ... | 1.00 |
```

Rules:
- Rows are read top to bottom; `bars` is `start-end` (inclusive start, exclusive end).
- Ranges should be contiguous and the last row's end should equal `bars`.
- A cell is that stem's **gain during that range**: `1.00` = full, `0.50` = quieter,
  `0.00` = muted.
- Gains are relative - the mix is re-normalised to -13 LUFS afterwards, so balance
  things against *each other*.

**4. Pan** - where each stem sits in the stereo field.

```markdown
| stem | mode   | left | right |
|------|--------|------|-------|
| hat  | stereo | 0.62 | 0.38  |   # leaked left
| ohat | stereo | 0.38 | 0.62  |   # leaked right
| perc | haas   |      |       |   # centred + Haas width
| kick | center |      |       |
```

`mode` is `center` (both channels, full level), `haas` (centred + a Haas widener),
or `stereo` (uses the `left`/`right` gains).

**5. Effects** - global mix parameters (all optional; omit a row to keep its default).

```markdown
| effect              | value | what it does |
|---------------------|-------|--------------|
| reverb_send         | 0.7   | level into the reverb bus |
| reverb_hpf          | 300   | high-pass on the send (keeps bass out of the reverb) |
| reverb_wet          | 1.0   | reverb return level |
| sidechain_threshold | 0.03  | kick side-chain: level at which ducking starts |
| sidechain_ratio     | 12    | ducking strength |
| sidechain_attack    | 5     | ducking attack (ms) |
| sidechain_release   | 120   | ducking release (ms) |
| stereo_width        | 1.3   | bus stereo widener |
| bus_threshold       | 0.1   | master bus compressor threshold |
| bus_ratio           | 3     | bus compressor ratio |
| bus_attack          | 10    | bus compressor attack (ms) |
| bus_release         | 150   | bus compressor release (ms) |
```

**6. Patterns** - the beats themselves. Each row is one bar of 16 steps (16th
notes): `x` = hit, `1`-`9` = velocity, `.` = rest. These gate the drum stems
sample-accurately, so this is where you reprogram the groove.

```markdown
| stem   | pattern          |
|--------|------------------|
| kick   | x...x...x...x... |
| clap   | ....x.......x... |
| hat    | xxxxxxxxxxxxxxxx |
| ohat   | ..x...x...x...x. |
| perc   | xx.x.xx.xx.x.xx. |
| bongo  | ..x.x..x..x.x..x |
| rim    | .x...x...x...x.. |
| shaker | ..x...x...x...x. |
```

`fftechno/arrangement.py` gate the drum stems with a sample-accurate `aeval`
multiplier, so the pattern fully defines *which* 16ths hit (the instruments run
free on the 16th grid; the pattern selects).

**7. Levels** - fixed level for stems that are not arranged per-section (the vocals
and the beeps; their timing lives in their own graphs).

```markdown
| stem  | level |
|-------|-------|
| vox   | 1.0   |
| beeps | 1.0   |
```

Times are in **bars** (1 bar = 4 beats at `bpm`). `fftechno/arrangement.py` turns
the tables into per-stem `volume=...:eval=frame` automation, adds panning / the kick
side-chain / the reverb bus, and writes the graph to `output/logs/mix.txt`.

### Worked examples

**Drop the kick for a breakdown (bars 40-56).** Insert a row and mute the drums:

```markdown
| 40-56   | 0.00 | 0.00 | 0.45 | 0.30 | 0.55 | ... | 1.10 |
```

**Bring the acid in later.** Set its intro cell to `0.00`.

**Solo the bass.** Set every other stem to `0.00` in a row.

**Change the groove.** Edit a drum row in **Patterns** - e.g. `x..x..x...x..x..`
for a broken kick, or `x..x..x..x..x..x` for a shuffled hat. Any stem in the
Patterns table is reprogrammed without touching any filter file.

**Change the tempo.** Set `bpm: 145` - durations follow automatically; the number of
bars (and so the length) is unchanged.

**Make it longer.** Raise `bars`, then extend/renumber the section rows to match.

**Balance the kit.** Nudge the Boosts (e.g. `kick: 2.8`) - boosts are global, whereas
section cells are per-section.

### Adding a brand-new sound (advanced)

1. **Define the synth** in `sounds.md` and generate its graph with
   `python -m fftechno synth` (writes `filters/<name>.txt`).
2. **Register it as a stem** in `fftechno/config.py`: add the name to `OSC_STEMS`
   (so it gets rendered) and to `MIX_INPUTS` (so it has an input index); add a `Pan`
   row for it.
3. **Give it a column** in the `song.md` Sections table and set its gains.
4. `python -m fftechno audio`.

### `sounds.md` + `templates/` reference

There are no built-in defaults: every value comes from `sounds.md`.

- `templates/*.txt` are filtergraphs with `{{key}}` placeholders.
- `sounds.md` global scalars (`sr`, `dur`, `lp`, `osr`, `bar`, `step`, `gold`,
  `vbase`, `vamt`, ...) apply to every instrument; an instrument's own `parameters`
  override or extend them.
- `python -m fftechno synth` substitutes the values and writes `filters/<name>.txt`;
  a missing placeholder fails loudly.

Templates: `kick`, `clap`, `noise` (hat/ohat/shaker), `tom` (perc/bongo), `rim`.

```markdown
step: 0.107143

| name | template | parameters |
| kick | kick.txt | amp=0.95, f0=48, sweep=220, rate=55, decay=24, click_amt=0.4, click_f=1200, ... |
```

The *beats* are not defined here - they come from the **Patterns** table in `song.md`.

### Command reference

| command | effect |
|---------|--------|
| `python -m fftechno audio` | rebuild `output/techno.wav` from `song.md` (vocals + IR + stems + mix + master) |
| `python -m fftechno synth` | write `filters/<name>.txt` for every instrument in `sounds.md` |
| `python -m fftechno video` | render the ASCII video from `output/techno.wav` (+ 720p preview) |
| `python -m fftechno video --static` | a single frozen frame (skip animation) |
| `python -m fftechno video --boost 2.0` | render and re-level the MP4 audio (video copied) |
| `python -m fftechno all` | audio, then video |
| `python -m fftechno boost 2.0` | re-level the existing MP4s only |

## Layout

```
fftechno/                 Python build tooling (stdlib only)
  config.py               paths, timing constants, stem lists, loudness targets
  proc.py                 subprocess helpers (quiet ffmpeg)
  audio.py                IR + stems + mix + 2-pass loudnorm master
  arrangement.py          parses song.md -> mix filtergraph (sections/pans/sidechain)
  vox.py                  espeak-ng phrases -> vocal stem
  video.py                vspipe|ffmpeg render, 720p preview, re-level
  cli.py                  `python -m fftechno ...`
filters/                  ffmpeg filter graphs (the actual synthesis)
  kick clap hat ohat perc shaker bongo rim bass growl acid beeps .txt
  vox.txt                 vocal placement graph
templates/                {{key}} filter-graph templates (kick/clap/noise/tom/rim)
sounds.md                 instrument definitions (template + parameters; no defaults)
song.md                   the arrangement (edit this; mix.txt is generated)
visualizer.vpy            VapourSynth + GLSL (ASCII art + B/W Berlin overlay)
pyproject.toml            package metadata / console script
tools/                    espeak-ng (gitignored)
ascii/                    source images (gitignored)
output/                   techno.wav, techno_visualizer*.mp4, stems/, logs/
```

Every `filters/*.txt` is an ffmpeg `-filter_complex_script` graph ending in `[out]`.
There is no hand-written `master.txt` - the master graph is generated in
`fftechno/audio.py` from the loudnorm measurements.

## How it works (short)

- **Sequencing without a sequencer.** `aevalsrc` per-sample expressions + `mod(t,period)`.
- **Hardgroove, 140 BPM, 4:00.** Punchy kick, offbeat open hats, tom/bongo
  percussion, shaker, rolling bass, arranged with per-stem `volume` automation.
- **303 acid.** Saw with a per-16th pattern, a real resonant 24 dB/oct low-pass,
  and a bright/dark filter crossfade for movement.
- **Granular robotic speech.** FM carrier x grain train x per-slot syllable window.
- **Vocals + beeps.** Female espeak-ng phrases, and a Win-startup-style bell arpeggio.
- **Quality.** Oscillators oversampled to 192 kHz then anti-alias filtered;
  `afir` convolution reverb; layering; groove velocity; dither.

## License

Released under the **PolyForm Noncommercial License 1.0.0** - see [`LICENSE`](LICENSE).
Noncommercial use only (personal, hobby, research, evaluation); any commercial use
requires a separate license from the copyright holder.

## Verify

```powershell
ffmpeg -hide_banner -i output/techno.wav -filter_complex ebur128=peak=true -f null -
ffprobe output/techno_visualizer.mp4
```
