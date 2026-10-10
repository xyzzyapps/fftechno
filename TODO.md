# TODO - ffmpeg_techno

Goal: build a techno beat + a granular robotic growl, synthesized entirely by
ffmpeg (no Python, no external synths). Multi-pass: render stems, then mix/master.

## Constants
- BPM 130, 4/4, 8 bars, 48 kHz, stereo WAV
- beat=0.461538s  eighth=0.230769s  sixteenth=0.115385s  bar=1.846154s
- total=14.769231s

## Plan / status
- [x] Environment check (ffmpeg filters, git init, folder layout)
- [x] Scaffold dirs: filters/, output/, output/stems/, output/logs/
- [x] filter scripts (each ends in `[out]`, one source -> wav):
  - [x] filters/kick.txt        (pitch-sweep sine, 4-on-floor)
  - [x] filters/clap.txt        (noise burst on beats 2 & 4)
  - [x] filters/hat.txt         (short hp-noise on 16ths)
  - [x] filters/bass.txt        (saw, 16-step pattern)
  - [x] filters/growl.txt       (granular grain-train * FM carrier * ring-mod -> robotic growl)
  - [x] filters/mix.txt         (5 stems -> sidechain duck vs kick -> bus)
  - [x] filters/master.txt      (two-pass linear loudnorm)
- [x] validate each script standalone (`-v error -f null -`)
- [x] render stems to output/stems/*.wav
- [x] mix/master to output/techno.wav
- [x] debug pass: astats/ebur128/ffprobe, determinism check
- [x] trim clap/hat level (were +1.3/+2.0 dBFS)
- [x] two-pass linear loudnorm (single-pass was fine but linear is cleaner)
- [x] build.ps1 runner
- [x] docs: README.md, SPEC.md
- [x] git commit

## Verified results
- output/techno.wav: pcm_s16le, 48 kHz, stereo, 14.769 s
- integrated loudness -14.0 LUFS, true peak -1.8 dBFS, no clips
- deterministic (framecrc identical across renders)

## Notes / risks
- ffmpeg eval has no user vars -> sub-expressions repeated inline.
- commas inside eval expressions protected by single quotes in the graph.
- `mod()` uses positive offsets to avoid sign surprises.
- re-measure loudnorm values in filters/master.txt if tempo/pattern changes.
