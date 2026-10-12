# Changelog

## v0.2

**Tracks**
- **"Basement" - jungle techno** (155 BPM, 155 bars = 4:00): a second full track,
  now the active `song.md`/`sounds.md`. 16 instruments (kick, snare, snarefill,
  clap, hat, ohat, ride, crash, breakbeat, conga, shaker, reese, acid, lead_pwm,
  lead_fm, pad, stab) plus a **vox** stem; sidechain on the kick, `reese` low bus.
- **Improved 303** (`acid.txt`): per-step accents, high-pass and a resonant peak;
  an F-based line with octave skips and slides.
- Hardgroove track (140 BPM) preserved in git history / earlier releases.

**Vocals**
- Short 1-3 word phrases (`config.VOX_LINES`), placed by `filters/vox.txt`.
- Local neural TTS, offline: **Kitten TTS** (default, `kittenml` nano ONNX model)
  or **Piper** - `python -m fftechno audio --tts kitten|piper`.

**Video** (`--look edge|pollock|outline`)
- **outline** (default here): silhouette contour only, crowd removed, blue hair
  chroma-keyed, random stills cut in on the beat; the shader keeps the colour.
- **pollock**: all-over abstract "painting" from whole-frame edges.
- **edge**: clean white line drawing of the matted subject.
- **On-screen lyrics**, timed from the same list that places the vocals (drawn
  with a self-contained 5x7 bitmap font - no font file/libass).

**Tooling**
- Optional **`--safe`** ear-protection limiter (off by default).
- **ffmpeg 9** support: filtergraphs read with `-/filter_complex FILE`.
- Outputs are never overwritten - a rebuild writes `_v2`/`_v3` names.
- Reproducible build lock; non-clobbering master/stems/video.

## v0.1

- Hardgroove techno track (140 BPM) synthesised entirely by ffmpeg from
  `song.md` + `sounds.md` via `templates/`; a black-and-white ASCII VapourSynth
  video; espeak-ng vocals; lossless markdown-driven port.
