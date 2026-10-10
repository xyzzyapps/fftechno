# ffmpeg_techno

A **two-minute hardgroove techno track** with a **granular robotic-speech** voice
and a **303 acid** line, synthesized **entirely by ffmpeg** (no DAW, no sampler),
plus a **VapourSynth + GLSL (vs-placebo)** Shadertoy-style visualizer combined into
a final video.

Outputs:
- `output/techno.wav` - 48 kHz stereo, 2:00, **-14.0 LUFS**, **-1.6 dBFS** true peak
- `output/techno_visualizer.mp4` - 1920x1080 30 fps, shader visual (~168 MB)
- `output/techno_visualizer_720p.mp4` - web preview (~79 MB)

## Requirements

- `ffmpeg` / `ffprobe` on `PATH` (gyan.dev full build: needs `aevalsrc`, `acrusher`,
  `asoftclip`, `sidechaincompress`, `alimiter`, `loudnorm`, `equalizer`, `highpass`,
  `lowpass`, `acompressor`).
- PowerShell (to run the build scripts; you can also call ffmpeg by hand).
- For the video: a local venv with `vapoursynth`, `numpy`, `vs-placebo`.

## Build the audio

```powershell
pwsh -File build.ps1
```

Raw commands (all `build.ps1` does):

```powershell
foreach ($s in 'kick','clap','hat','ohat','perc','bass','growl','acid') {
  ffmpeg -hide_banner -v error -filter_complex_script "filters/$s.txt" `
    -map "[out]" -c:a pcm_f32le "output/stems/$s.wav" -y
}
ffmpeg -hide_banner -v error `
  -i output/stems/kick.wav -i output/stems/clap.wav -i output/stems/hat.wav `
  -i output/stems/ohat.wav -i output/stems/perc.wav -i output/stems/bass.wav `
  -i output/stems/growl.wav -i output/stems/acid.wav `
  -filter_complex_script filters/mix.txt -map "[out]" -c:a pcm_f32le output/mix_pre.wav -y
ffmpeg -hide_banner -v error -i output/mix_pre.wav `
  -filter_complex_script filters/master.txt -map "[out]" -c:a pcm_s16le output/techno.wav -y
```

## Build the video

```powershell
python -m venv .venv
.venv\Scripts\pip install vapoursynth numpy vs-placebo
.venv\Scripts\vapoursynth config        # one-off: registers Python paths for vspipe
pwsh -File build_video.ps1
```

## Layout

```
filters/kick.txt    punchy 4-on-the-floor kick
filters/clap.txt    clap on 2 & 4
filters/hat.txt     closed 16th hats
filters/ohat.txt    offbeat open hat
filters/perc.txt    syncopated toms/congas
filters/bass.txt    rolling saw bass
filters/growl.txt   granular robotic-speech voice
filters/acid.txt    303 acid line (resonant saw, accents, slides)
filters/mix.txt     8 stems + section automation -> sidechain -> bus
filters/master.txt  two-pass linear loudnorm + limiter -> final
build.ps1           audio passes
visualizer.vpy      VapourSynth + GLSL shader visual
build_video.ps1     vspipe -> ffmpeg mux/encode -> MP4
output/             techno.wav, techno_visualizer*.mp4, stems/, logs/
```

Each `filters/*.txt` is an ffmpeg `-filter_complex_script` graph ending in `[out]`.

## How it works (short version)

- **Sequencing without a sequencer.** `aevalsrc` evaluates a math expression per
  sample; `mod(t, period)` turns it into a repeating pattern (kick every beat,
  closed hats every 16th, offbeat open hat on the "&", clap on 2 & 4, toms on a
  syncopated pattern).
- **Hardgroove.** 140 BPM, punchy kick, offbeat open hats, tribal toms, rolling
  16th bass. **70 bars / 2:00**, arranged with per-stem `volume` automation
  (`eval=frame`) into intro / main / break / main2 / outro.
- **303 acid.** A saw oscillator with a per-16th pitch pattern, accent steps and a
  per-note pitch-bend "squawk", then resonant `equalizer` peaks + `asoftclip`
  overdrive + `acrusher` -> acid.
- **Granular robotic speech.** A formant-rich FM carrier multiplied by a grain
  train and a per-slot syllable window, with a per-grain pitch contour, ring mod
  and formant EQ.
- **Glue.** Kick keys a `sidechaincompress` on the bass+voice bus; the master is
  linearly normalised to -14 LUFS with a true-peak limiter.

See `SPEC.md` for the full spec, expressions and diagrams.

## Visualizer + final video (VapourSynth + GLSL)

`visualizer.vpy` runs a real GLSL shader via **vs-placebo** (`core.placebo.Shader`):
- VapourSynth writes a small audio data-strip (64 spectrum bands + bass + kick +
  energy) into the top rows of a YUV444P16 clip each frame.
- A Shadertoy-style procedural shader - a rotating kaleidoscopic neon tunnel with a
  glowing core, audio-reactive spokes/rays, kick glitches and grain - generates the
  whole visual. libplacebo custom shaders have no `iTime`, but vs-placebo exposes
  the `frame` uniform, so the shader animates on `float(frame)/FPS`; it reads the
  strip via `HOOKED_tex` for audio reactivity.
- A two-digit 7-segment **countdown numeral** (70 -> 1, one per bar) is overlaid.

The shader runs on the GPU (~60 fps), so the full 2-minute render is a few minutes.

Verify: `ffprobe output/techno_visualizer.mp4`.
