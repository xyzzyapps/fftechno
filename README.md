# fftechno

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

The arrangement is per-stem gain automation in `filters/mix.txt` (volume follows
time with `eval=frame`). Seven regions:

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

## Editing the arrangement (`song.md`)

The arrangement is **user-programmable** in `song.md` - a plain markdown file.
`python -m fftechno audio` regenerates the mix graph from it, so there is no hand
-edited `mix.txt` to maintain.

`song.md` has three parts:

1. **Scalars** - `bpm`, `bars`, `fade_bars` (the final section fades to silence
   over this many bars).
2. **Boosts** table - a per-stem gain applied on top of the section gains (used to
   balance the kit, e.g. `kick: 2.55`).
3. **Sections** table - one row per section (`bars` range) and one column per
   arranged stem; each cell is that stem's gain in that section (`0.00` mutes it).

```
| bars    | kick | clap | hat  | ohat | ... | acid |
|---------|------|------|------|------|-----|------|
| 0-8     | 0.90 | 0.00 | 0.50 | 0.00 | ... | 0.80 |
| 8-32    | 1.00 | 0.70 | 0.55 | 0.50 | ... | 0.90 |
```

Times are in **bars** (1 bar = 4 beats at `bpm`). The Python turns the table into
per-stem `volume=...:eval=frame` automation (`fftechno/arrangement.py`), adds the
panning / kick side-chain / reverb bus, and writes `output/logs/mix.txt`.

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

## Verify

```powershell
ffmpeg -hide_banner -i output/techno.wav -filter_complex ebur128=peak=true -f null -
ffprobe output/techno_visualizer.mp4
```
