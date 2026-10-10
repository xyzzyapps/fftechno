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

## Layout

```
fftechno/                 Python build tooling (stdlib only)
  config.py               paths, timing constants, stem lists, loudness targets
  proc.py                 subprocess helpers (quiet ffmpeg)
  audio.py                IR + stems + mix + 2-pass loudnorm master
  vox.py                  espeak-ng phrases -> vocal stem
  video.py                vspipe|ffmpeg render, 720p preview, re-level
  cli.py                  `python -m fftechno ...`
filters/                  ffmpeg filter graphs (the actual synthesis)
  kick clap hat ohat perc shaker bongo rim bass growl acid beeps .txt
  mix.txt                 section automation + sidechain + reverb bus
  vox.txt                 vocal placement graph
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
