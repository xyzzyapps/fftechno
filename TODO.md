# TODO - ffmpeg_techno

Deliverables:
1. A hardgroove techno beat + granular robotic-speech voice, synthesized by ffmpeg.
2. A VapourSynth countdown visualizer, combined with the track into a final video.

## Track (audio) - DONE
BPM 140, 4/4, 8 bars, 48 kHz. beat=0.428571  eighth=0.214286  sixteenth=0.107143
bar=1.714286  half-bar=0.857143  total=13.714286

- [x] hardgroove kit: kick (punchy sweep), clap (2&4), closed hat (16ths),
      ohat (offbeat open hat), perc (syncopated toms), bass (rolling 16ths),
      growl (granular robotic-speech voice)
- [x] growl reworked from constant buzz -> per-grain pitch contour + syllable
      windows + formants so it reads as robotic speech
- [x] mix: 7 stems, kick sidechain ducks bass+voice bus
- [x] master: 2-pass linear loudnorm + alimiter (level=disabled) -> -14.4 LUFS,
      -1.5 dBFS true peak
- [x] verified: scripts valid, deterministic, waveform/spectrum proofs

## Visualizer video - DONE
- [x] local venv + vapoursynth numpy (R81 abi3 on Py3.14); `vapoursynth config`
- [x] visualizer.vpy: numpy STFT + film-leader countdown (sweep hand, crosshair,
      7-segment numerals 8..1 per bar, grain, scratch flicker, kick strobe/jitter,
      amber spectrum bars)
- [x] build_video.ps1: vspipe -> ffmpeg mux/encode -> MP4 (+ 720p preview)
- [x] output/techno_visualizer.mp4 (~46 MB) + 720p (~10 MB)
- [x] docs updated (README, SPEC)

## Notes / risks
- ffmpeg eval has no user vars -> constants repeated inline; BPM change ripples
  through every filter file and `BAR` in visualizer.vpy.
- Visualizer drawing pass ~2.7 fps -> full clip ~2.5 min.
- `vspipe` needs `vapoursynth config` once (writes %APPDATA%\vapoursynth).
- Re-measure loudnorm values in filters/master.txt if tempo/pattern changes.
- `alimiter` must use `level=disabled` (default auto-level boosts over ceiling).
