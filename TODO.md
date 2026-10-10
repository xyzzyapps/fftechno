# TODO - ffmpeg_techno

Deliverables:
1. A 2-minute hardgroove techno track + granular robotic-speech voice + 303 acid,
   synthesized by ffmpeg.
2. A VapourSynth + GLSL (vs-placebo) Shadertoy-style visual, combined into a video.

## Audio - DONE
BPM 140, 70 bars, 2:00. beat=0.428571  sixteenth=0.107143  bar=1.714286
- [x] hardgroove kit: kick, clap, closed hat, offbeat open hat (ohat),
      syncopated toms (perc), rolling bass, granular robotic-speech voice (growl)
- [x] 303 acid line (acid): per-16th pitch pattern, accents, per-note bend squawk,
      resonant EQ + overdrive + acrusher
- [x] 2-minute arrangement via per-stem `volume` automation (eval=frame):
      intro / main1 / break / main2 / outro
- [x] mix: 8 stems, kick sidechain ducks bass+voice bus
- [x] master: 2-pass linear loudnorm + alimiter -> -14.0 LUFS, -1.6 dBFS TP

## Video - DONE
- [x] venv + vapoursynth numpy vs-placebo (R81 abi3 on Py3.14)
- [x] visualizer.vpy: numpy audio strip -> YUV444P16 -> core.placebo.Shader (GLSL
      kaleidoscopic neon acid tunnel, `frame` for time, `random`, strip for audio)
      -> 7-segment countdown numeral (70..1) overlay -> YUV420P8
- [x] fixed: shader output matrix (matrix=5) + resize matrix_in_s for colorspace path
- [x] build_video.ps1 -> output/techno_visualizer.mp4 (1080p, 120 s) + 720p preview
- [x] docs updated (README, SPEC)

## Notes / risks
- ffmpeg eval has no user vars; tempo changes ripple through every filter + `BAR`.
- vs-placebo Shader needs a Vulkan GPU (AMD RX 6800M, ~60 fps).
- custom shaders are not raw Shadertoy: use `frame` for time, HOOKED_tex for input.
- re-measure loudnorm in filters/master.txt after any tempo/pattern change.
- `alimiter` must use `level=disabled`.
- .gitignore now excludes output/stems, output/*.mp4, output/logs (too large for git).
