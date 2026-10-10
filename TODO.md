# fftechno - TODO / status

4-minute hardgroove techno track (ffmpeg-only synthesis) + B/W ASCII video.
Tooling is pure Python (`fftechno/` package); no shell scripts.

## Audio - DONE
BPM 140, 140 bars, 4:00. Stems: kick, clap, hat, ohat, perc, shaker, bongo, rim,
bass, growl, acid, beeps (+ espeak-ng female vox).

- [x] hardgroove kit + offbeat hats + toms + bongo + rim + shaker
- [x] 303 acid: bright/dark sweep + real resonant 24 dB/oct low-pass
- [x] granular robotic-speech voice
- [x] female espeak-ng vocals (9 phrases x 3 placements)
- [x] Win-startup-style beep arpeggio
- [x] 4-minute arrangement (per-stem volume automation)
- [x] quality: 192 kHz oversampling, afir convolution reverb, layering,
      groove velocity, per-element saturation, dither
- [x] drums boosted; bass ducked; master -13.0 LUFS / -1.0 dBFS

## Video - DONE
- [x] ASCII images from ascii/ + B/W Berlin overlay (GLSL via vs-placebo)
- [x] every image used at least 3 times (shuffled REUSE=3 playlist)
- [x] final MP4 audio re-leveled (boost command)

## Tooling - DONE
- [x] replaced PowerShell with the `fftechno` Python package (stdlib only)
- [x] removed build.ps1 / build_video.ps1 / make_vox.ps1
- [x] removed filters/master.txt (master graph generated in Python)
- [x] visualizer.vpy de-cluttered
- [x] pyproject.toml + `python -m fftechno` CLI

## Notes / risks
- 192 kHz stem generation is slow (~8 min for 12 stems).
- Re-run `python -m fftechno audio` after any mix/filter change.
- gitignore excludes .venv, tools/, ascii/, __pycache__, output/stems, output/*.mp4.
- Remaining gap vs a DAW: ffmpeg IIR filters can't be automated per sample; no true
  swing; near-single-voice synths. Closing that needs a real synth engine (still
  sample-free).

- [x] programmable arrangement via song.md (fftechno/arrangement.py; filters/mix.txt removed)

- [x] markdown instrument definitions (sounds.md + fftechno/synth.py; kick/noise generators)
