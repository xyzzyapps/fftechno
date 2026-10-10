# ffmpeg_techno

A **hardgroove techno beat** with a **granular robotic-speech** voice, synthesized
**entirely by ffmpeg**. There is no Python, no DAW, no sampler and no external
synth: every sound is an ffmpeg `eval` expression (`aevalsrc`) plus native DSP
filters, sequenced by modulo-gated envelopes.

Output: `output/techno.wav` - 48 kHz stereo, 8 bars @ 140 BPM (13.77 s),
-14.4 LUFS integrated, -1.5 dBFS true peak.

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
foreach ($s in 'kick','clap','hat','ohat','perc','bass','growl') {
  ffmpeg -hide_banner -v error -filter_complex_script "filters/$s.txt" `
    -map "[out]" -c:a pcm_f32le "output/stems/$s.wav" -y
}

# 2) mix + sidechain duck  -> output/mix_pre.wav
ffmpeg -hide_banner -v error `
  -i output/stems/kick.wav -i output/stems/clap.wav -i output/stems/hat.wav `
  -i output/stems/ohat.wav -i output/stems/perc.wav `
  -i output/stems/bass.wav -i output/stems/growl.wav `
  -filter_complex_script filters/mix.txt -map "[out]" -c:a pcm_f32le output/mix_pre.wav -y

# 3) master (2-pass linear loudnorm) -> output/techno.wav
ffmpeg -hide_banner -v error -i output/mix_pre.wav `
  -filter_complex_script filters/master.txt -map "[out]" -c:a pcm_s16le output/techno.wav -y
```

To audition a single instrument, render just its stem (step 1) and play the WAV.

## Layout

```
filters/kick.txt    punchy pitch-swept sine kick, 4-on-the-floor
filters/clap.txt    noise burst on beats 2 & 4
filters/hat.txt     short high-passed noise on 16ths (closed hat)
filters/ohat.txt    offbeat open hat (on the "&" of every beat)
filters/perc.txt    syncopated pitched toms/congas (tribal groove)
filters/bass.txt    rolling saw bass, 16-step pattern (low-passed)
filters/growl.txt   granular robotic-speech voice  <-- the centrepiece
filters/mix.txt     7 stems -> sidechain duck vs kick -> bus
filters/master.txt  two-pass linear loudnorm + limit -> final
build.ps1           runs the three passes
output/             techno.wav, stems/, mix_pre.wav, logs/ (spectra, proofs)
```

Each `filters/*.txt` is an ffmpeg `-filter_complex_script` graph (a source and
effects ending in the label `[out]`).

## How it works (short version)

- **Sequencing without a sequencer.** `aevalsrc` evaluates a math expression per
  sample. A local time `mod(t, period)` turns a continuous expression into a
  repeating pattern (kick every beat, closed hats every 16th, offbeat open hat on
  the "&", clap on 2 & 4, toms on a syncopated 16th pattern).
- **Hardgroove.** 140 BPM, a punchy pitch-swept kick, offbeat open hats and
  pitched tom/conga accents over a rolling 16th bass give the driving hardgroove
  feel.
- **Granular robotic speech.** The voice multiplies a formant-rich FM carrier by a
  *grain train* (four overlapping Hann grains, `w(x)=sin(PI*x)^2`) and by a
  per-slot syllable window. A per-grain pitch contour (`1.00, 1.19, 1.08, ...`)
  gives speech-like intonation; ring modulation adds the robot; formant
  `equalizer` bumps, `acrusher` and `asoftclip` finish it.
- **Glue.** Kick keys a `sidechaincompress` on the bass+voice bus; the master is
  compressed, limited and normalised to -14 LUFS / -1 dBTP.

See `SPEC.md` for the full specification, diagrams and the exact expressions.

## Visualizer + final video (VapourSynth)

`visualizer.vpy` is a VapourSynth script that renders an audio-reactive visual
from `output/techno.wav` in a **film-leader "countdown" style**: heavy grain, a
rotating sweep hand (one revolution per bar) with crosshair, a large 7-segment
numeral counting down 8..1 one per bar, occasional scratch flicker, kick strobes
and jitter, and the spectrum as amber audio-reactive bars along the bottom.
`ffmpeg` muxes the audio and encodes.

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

- `output/techno_visualizer.mp4` - 1920x1080, 30 fps, H.264 CRF 20, AAC 192k (~46 MB)
- `output/techno_visualizer_720p.mp4` - web preview, 1280x720 CRF 22 (~10 MB)
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
