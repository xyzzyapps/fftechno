# ffmpeg_techno

A **techno beat** with a **granular robotic growl**, synthesized **entirely by ffmpeg**.
There is no Python, no DAW, no sampler and no external synth: every sound is an
ffmpeg `eval` expression (`aevalsrc`) plus native DSP filters, sequenced by
modulo-gated envelopes.

Output: `output/techno.wav` - 48 kHz stereo, 8 bars @ 130 BPM (14.769 s),
-14 LUFS integrated, -1.8 dBFS true peak.

## Requirements

- `ffmpeg` / `ffprobe` on `PATH` (verified with the gyan.dev full build; needs
  `aevalsrc`, `acrusher`, `asoftclip`, `sidechaincompress`, `alimiter`,
  `loudnorm`, `equalizer`, `highpass`, `lowpass`, `acompressor`).
- PowerShell (only to run the optional `build.ps1`; you can also call ffmpeg by hand).

## Build

```powershell
pwsh -File build.ps1
```

Or run the raw commands (this is all `build.ps1` does):

```powershell
# 1) stems
foreach ($s in 'kick','clap','hat','bass','growl') {
  ffmpeg -hide_banner -v error -filter_complex_script "filters/$s.txt" `
    -map "[out]" -c:a pcm_f32le "output/stems/$s.wav" -y
}

# 2) mix + sidechain duck  -> output/mix_pre.wav
ffmpeg -hide_banner -v error `
  -i output/stems/kick.wav -i output/stems/clap.wav -i output/stems/hat.wav `
  -i output/stems/bass.wav -i output/stems/growl.wav `
  -filter_complex_script filters/mix.txt -map "[out]" -c:a pcm_f32le output/mix_pre.wav -y

# 3) master (2-pass linear loudnorm) -> output/techno.wav
ffmpeg -hide_banner -v error -i output/mix_pre.wav `
  -filter_complex_script filters/master.txt -map "[out]" -c:a pcm_s16le output/techno.wav -y
```

To audition a single instrument, render just its stem (step 1) and play the WAV.

## Layout

```
filters/kick.txt    pitch-swept sine, 4-on-the-floor
filters/clap.txt    noise burst on beats 2 & 4
filters/hat.txt     short high-passed noise on 16ths
filters/bass.txt    saw bass, 16-step pattern (low-passed)
filters/growl.txt   granular robotic growl  <-- the centrepiece
filters/mix.txt     5 stems -> sidechain duck vs kick -> bus
filters/master.txt  two-pass linear loudnorm + limit -> final
build.ps1           runs the three passes
output/             techno.wav, stems/, mix_pre.wav, logs/ (spectra, proofs)
```

Each `filters/*.txt` is an ffmpeg `-filter_complex_script` graph (a source and
effects ending in the label `[out]`).

## How it works (short version)

- **Sequencing without a sequencer.** `aevalsrc` evaluates a math expression per
  sample. A local time `mod(t, period)` turns a continuous expression into a
  repeating pattern (kick every beat, hats every 16th, clap on 2 & 4).
- **Granular synthesis without a granular filter.** The growl multiplies a
  carrier by a *grain train*: the sum of four shifted windowed grains
  `w(x)=sin(PI*x)^2` at a 0.018 s hop and 0.05 s grain length, so grains overlap
  into a cloud.
- **Robotic.** The cloud is ring-modulated by `0.5+0.5*sin(2*PI*137*t)` and the
  carrier is FM'd (`sin(2*PI*(55t + 6*sin(2*PI*7t)))`), then shaped by formant
  `equalizer` bumps, bit/sample-crushed by `acrusher`, saturated by `asoftclip`.
- **Glue.** Kick keys a `sidechaincompress` on the bass+growl bus; the master is
  compressed, limited and normalised to -14 LUFS / -1 dBTP.

See `SPEC.md` for the full specification, diagrams and the exact expressions.

## Visualizer + final video (VapourSynth)

`visualizer.vpy` is a VapourSynth script that renders an audio-reactive visual
from `output/techno.wav` - dark Berlin warehouse: hypnotic bass-reactive rings, a
receding perspective floor grid, 64 neon spectrum tubes with a wet-floor
reflection and peak-hold caps, an oscilloscope trace, kick-driven strobes and
chromatic glitch, scanlines and film grain. `ffmpeg` muxes the audio and encodes.

The visualizer needs a local venv (one-off setup):

```powershell
python -m venv .venv
.venv\Scripts\pip install vapoursynth numpy
.venv\Scripts\vapoursynth config   # one-off: registers Python paths for vspipe
```

Build the video:

```powershell
pwsh -File build_video.ps1
```

Outputs / verify:

- `output/techno_visualizer.mp4` - 1920x1080, 30 fps, H.264 CRF 20, AAC 192k (~120 MB)
- `output/techno_visualizer_720p.mp4` - web preview, 1280x720 CRF 22 (~19 MB)
- `ffprobe output/techno_visualizer.mp4`

Tweak the look via the constants at the top of `visualizer.vpy` (W, H, FPS,
NBARS, palette). The drawing pass runs ~2 fps, so a full clip takes a few minutes.

## Verify

```powershell
# loudness + true peak
ffmpeg -i output/techno.wav -filter_complex ebur128=peak=true -f null -

# quickly validate any filter graph without encoding
ffmpeg -v error -filter_complex_script filters/growl.txt -map "[out]" -f null -
```
