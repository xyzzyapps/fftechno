# TODO - ffmpeg_techno

3-minute hardgroove techno track (ffmpeg-only) + B/W ASCII VapourSynth visual.

## Audio - DONE
BPM 140, 105 bars, 3:00. Stems: kick, clap, hat, ohat, perc, shaker, bongo, rim,
bass, growl, acid (+ espeak-ng female vox). No stab, no acid2 (removed by request).

- [x] hardgroove kit + offbeat hats + syncopated toms + bongo + rim + shaker
- [x] 303 acid with a time-automated bright/dark filter crossfade ("knob")
- [x] granular robotic-speech voice
- [x] female espeak-ng vocals ("speak to me", "come on", "feel it", "hard groove"),
      pitch tuned down from the too-high version
- [x] 3-minute arrangement via per-stem `volume` automation (eval=frame)
- [x] stereo depth (panning + haas + extrastereo, mid ~4 dB above side)
- [x] master: 2-pass loudnorm + limiter + tone + dither -> -14.0 LUFS / -1.9 dBFS

### Quality pass ("closer to Ableton", no samples)
- [x] **Oversampling / anti-aliasing**: oscillators generated at 192 kHz, low-passed
      at 19 kHz, downsampled to 48 kHz (removes folded aliasing).
- [x] **Convolution reverb**: synthesized IR (decaying noise, no sample) + `afir`
      on a high-passed send bus.
- [x] **Layering**: kick sub-octave + noise transient; bass detuned unison layer.
- [x] **Per-element saturation**: `asoftclip` on kick/bass.
- [x] **Groove velocity**: golden-angle per-step amplitude on hats/perc/shaker/
      bongo/rim.
- [x] **Master polish**: high-shelf tone + triangular-HP dither.

## Video - DONE
- [x] venv + vapoursynth numpy vs-placebo
- [x] ASCII images from ascii/ (numpy 5x7 font), random image per beat (rapid),
      B/W Berlin overlay via GLSL shader (frame + audio strip)
- [x] build_video.ps1 -> output/techno_visualizer.mp4 (+ 720p preview)

## Notes / risks
- 192 kHz stem generation is slow (~6 min for all stems).
- Re-measure loudnorm in filters/master.txt after any mix change.
- Still ffmpeg-only; remaining gaps vs Ableton: no true per-voice resonant filter
  (303 uses a crossfade), no real swing, single-voice-ish synths.
- gitignore excludes tools/, ascii/, output/stems, output/*.mp4, output/logs.
