# TODO - ffmpeg_techno

4-minute hardgroove techno track (ffmpeg-only) + B/W ASCII VapourSynth visual.

## Audio
BPM 140, 140 bars, 4:00 (240 s). Stems: kick, clap, hat, ohat, perc, shaker,
bongo, rim, bass, growl, acid, beeps (+ espeak-ng female vox).

- [x] hardgroove kit + offbeat hats + toms + bongo + rim + shaker
- [x] 303 acid: bright/dark sweep + a real resonant 24 dB/oct low-pass
- [x] granular robotic-speech voice
- [x] female espeak-ng vocals, 9 phrases placed 3x each
- [x] Win-startup-style beep arpeggio
- [x] 4-minute arrangement (per-stem volume automation)
- [x] quality pass: oversampling (192k), afir convolution reverb, layering,
      groove velocity, per-element saturation, dither
- [x] drums boosted (kick/hat x2.55, clap x2.4, ohat x2.25, perc/bongo/rim x1.95,
      shaker x1.875), bass x0.75, harder sidechain
- [x] master -13.0 LUFS / -1.0 dBFS

## Video
- [x] ASCII images from ascii/, B/W Berlin overlay (GLSL via vs-placebo)
- [x] every image used at least 3 times (shuffled REUSE=3 playlist)
- [x] final MP4 audio boosted 150% (volume=1.5 + limiter, video copied)

## Notes / risks
- 192 kHz stem generation is slow (~8 min for 12 stems).
- Re-measure loudnorm in filters/master.txt after any mix change.
- gitignore excludes tools/, ascii/, output/stems, output/*.mp4, output/logs.
- Remaining gap vs Ableton: ffmpeg IIR filters can't be automated per sample
  (303 sweep is a crossfade + fixed resonant cascade); no true swing; near-single-
  voice synths. Closing that needs a real synth engine (still no samples).
