# ffmpeg_techno

A **three-minute hardgroove techno track** - granular robotic-speech voice, 303
acid line, and a spoken "speak to me" vocal - synthesized **entirely by ffmpeg**
(no DAW, no sampler), with a **black-and-white VapourSynth + GLSL** visual that
turns images into **ASCII art** and draws Berlin techno overlays on top, muxed
into a final video.

Outputs:
- `output/techno.wav` - 48 kHz stereo, 3:00, **-14.0 LUFS**, **-1.7 dBFS** true peak
- `output/techno_visualizer.mp4` - 1920x1080 30 fps, ASCII + B/W shader (~258 MB)
- `output/techno_visualizer_720p.mp4` - web preview (~128 MB)

## Requirements

- `ffmpeg` / `ffprobe` on `PATH` (gyan.dev full build).
- PowerShell (build scripts; ffmpeg can also be called by hand).
- Video: a local venv with `vapoursynth`, `numpy`, `vs-placebo`.
- Vocal: **espeak-ng** (downloaded into `tools/` by the setup below).

## Build the audio

```powershell
# one-off: fetch espeak-ng into tools/ (no system install)
mkdir tools
curl -L -o tools/espeak-ng.msi https://github.com/espeak-ng/espeak-ng/releases/download/1.52.0/espeak-ng.msi
msiexec /a tools\espeak-ng.msi /qn TARGETDIR="%CD%\tools\espeak-ng"

pwsh -File build.ps1
```

`build.ps1` = generate the vocal (`make_vox.ps1`) -> render 9 expression stems ->
mix (10 inputs) -> master.

## Build the video

```powershell
python -m venv .venv
.venv\Scripts\pip install vapoursynth numpy vs-placebo
.venv\Scripts\vapoursynth config        # one-off
pwsh -File build_video.ps1
```

Put images (jpg/png) in `ascii/`; the visualizer picks one at random every 2 bars,
converts it to ASCII art, and draws the B/W overlay.

## Layout

```
filters/kick clap hat ohat perc shaker bongo rim bass growl acid .txt  expression stems
filters/mix.txt     10 inputs + section automation -> sidechain -> bus
filters/master.txt  two-pass linear loudnorm + limiter
make_vox.ps1        espeak-ng vocal -> output/stems/vox.wav
build.ps1           vocal + stems + mix + master
visualizer.vpy      VapourSynth + GLSL (ASCII art + B/W Berlin overlay)
build_video.ps1     vspipe -> ffmpeg mux/encode -> MP4
tools/              espeak-ng (gitignored)
ascii/              source images (gitignored)
output/             techno.wav, techno_visualizer*.mp4, stems/, logs/
```

## How it works (short version)

- **Sequencing without a sequencer.** `aevalsrc` per-sample expressions + `mod(t,period)`.
- **Hardgroove, 140 BPM, 3:00 (105 bars).** Punchy kick, offbeat open hats,
  syncopated toms, shaker, rolling bass; arranged with per-stem `volume`
  automation (`eval=frame`) into intro/main/break/main2/break2/main3/outro.
- **303 acid.** Saw with a per-16th pattern, accents, per-note bend, and a
  **time-automated two-branch filter crossfade** (bright saw vs. dark low-passed)
  for a real moving "knob" sweep, plus resonant EQ + overdrive.
- **Granular robotic speech.** FM carrier x grain train x per-slot syllable window,
  per-grain pitch contour, ring mod, formant EQ.
- **Vocal.** espeak-ng "speak to me" pitched down, bit-crushed, reverbed, placed at
  section hits.
- **Stereo depth.** Per-stem panning + Haas + `extrastereo` (mid ~4 dB above side).
- **Glue.** Kick side-chains the bass+voice bus; master normalised to -14 LUFS.
- **Quality pass (no samples).** Oscillators are generated at **192 kHz** and
  anti-alias low-passed before downsampling to 48 kHz; a **convolution reverb**
  (synthesized decaying-noise IR via `afir`) adds space on a high-passed send;
  kick/bass are **layered** (sub-octave, noise transient, detuned unison); hats/
  perc get per-step **velocity**; the master adds a tone shelf + dither.

## Visualizer (VapourSynth + GLSL, B/W)

- Images from `ascii/` are decoded with ffmpeg and rendered to **ASCII art** with a
  self-contained numpy 5x7 bitmap font (no external deps), one random image per
  2-bar block.
- A GPU GLSL shader (vs-placebo) reads the ASCII (`HOOKED_tex`), the audio strip
  (64 bands + bass + kick + energy) and `frame` (time), and draws a **monochrome**
  Berlin overlay: hypnotic rings, audio spokes, grid, scanlines, kick glitch, grain.
- libplacebo custom shaders have no `iTime`, but vs-placebo exposes `frame`, so it
  animates; the shader output carries `matrix=5` so the follow-up resize has a path.

Verify: `ffprobe output/techno_visualizer.mp4`.
