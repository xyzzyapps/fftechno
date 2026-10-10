# TODO - ffmpeg_techno

Deliverables:
1. A techno beat + granular robotic growl, synthesized entirely by ffmpeg.
2. A VapourSynth visualizer, combined with the track into a final video.

## Track (audio) - DONE

Constants: BPM 130, 4/4, 8 bars, 48 kHz. beat=0.461538s  eighth=0.230769s
sixteenth=0.115385s  bar=1.846154s  total=14.769231s

- [x] Environment check (ffmpeg filters, git init, folder layout)
- [x] filter scripts (each ends in `[out]`):
  - [x] filters/kick.txt        (pitch-sweep sine, 4-on-floor)
  - [x] filters/clap.txt        (noise burst on beats 2 & 4)
  - [x] filters/hat.txt         (short hp-noise on 16ths)
  - [x] filters/bass.txt        (saw, 16-step pattern)
  - [x] filters/growl.txt       (granular grain-train * FM carrier * ring-mod)
  - [x] filters/mix.txt         (sidechain duck vs kick -> bus)
  - [x] filters/master.txt      (two-pass linear loudnorm)
- [x] validate scripts, render stems, mix/master
- [x] output/techno.wav: -14.0 LUFS, -1.8 dBFS true peak, deterministic
- [x] build.ps1 runner, README.md, SPEC.md

## Visualizer video - DONE

- [x] Create local venv + pip install vapoursynth numpy (R81, abi3 on Py3.14)
- [x] One-off `vapoursynth config` (writes %APPDATA%\vapoursynth\vapoursynth.toml)
- [x] Probe R81 frame API (frame.copy() + get_write_ptr().value + stride via ctypes)
- [x] visualizer.vpy: numpy STFT analysis + dark Berlin visual (rings, floor grid,
      neon bars + reflection, scope trace, kick strobe, chromatic glitch, grain)
- [x] fix matrix option (matrix_s only, no matrix_in_s) for RGB->YUV420P8
- [x] fix ModifyFrame callback signature (second arg must be named `f`)
- [x] tune kick strobe to cool white (was green)
- [x] build_video.ps1: vspipe -> ffmpeg mux/encode -> MP4
- [x] output/techno_visualizer.mp4 (1080p) + 720p web preview
- [x] docs updated (README, SPEC)
- [x] git commit

## Notes / risks
- ffmpeg eval has no user vars -> sub-expressions repeated inline (audio side).
- Visualizer drawing pass runs ~2 fps -> full clip ~3.5 min.
- The 1080p master is ~120 MB because of film grain; 720p preview is ~19 MB.
- vspipe needs `vapoursynth config` once; it writes a config file to %APPDATA%
  (the only artifact created outside the project folder).
- Re-measure loudnorm values in filters/master.txt if the tempo/pattern changes.
