# fftechno - status

Two four-minute techno tracks (all sound synthesized by ffmpeg) plus a
black-and-white dancing-girl music video, driven by markdown.

## Done

### Engine + tooling
- Markdown control surfaces: `song.md` (arrangement + mix) and `sounds.md`
  (instruments), rendered through `templates/` via `{{key}}` and
  `{{if_steps(seq; grid; default)}}`.
- Master: two-pass linear loudnorm -> -13.0 LUFS / -1.0 dBFS; optional
  **`--safe`** ear-protection limiter (off by default).
- Build lock; non-clobbering outputs (`config.unique_path` -> `_v2`/`_v3`).
- **ffmpeg 9**: filtergraphs read with `-/filter_complex FILE`.
- Voice: ffmpeg's built-in `flite` (`slt`) - no external espeak-ng; short phrases
  from `config.VOX_LINES`, which also drive the on-screen lyrics.
- Video (`fftechno/girl.py`, `matte.py`, `visualizer.vpy`): beat-locked dancing-girl
  loop with `--look edge|pollock|outline` (Pollock default) and `--mode
  reset|trail|build`. The **outline** look shows only the silhouette contour
  (no face interior, crowd removed) with the **blue hair chroma-keyed** and an
  **eye outline** (mask-derived, no ML), cuts random stills in **on the beat**,
  and burns the **lyrics** in at the vocal times; the shader preserves chroma.

### Track 1 - "hardgroove" (in git history, commit cb9741c)
- 140 BPM, 12 instruments (kick, clap, hat, ohat, conga, bongo, rim, shaker, bass,
  acid, growl, beeps), the ASCII video, later the Pollock rework.

### Track 2 - "Basement" jungle techno (current `song.md`/`sounds.md`)
- **155 BPM, 155 bars = 4:00**, sidechain on kick, `reese` low bus.
- **16 instruments**: kick, snare, snarefill, clap, hat, ohat, ride, crash,
  breakbeat, conga, shaker, reese, acid, lead_pwm, lead_fm, pad, stab - plus the
  **vox** stem (ffmpeg `flite`, short phrases with matching on-screen lyrics).
- New templates: `snare`, `ride`, `crash`, `breakbeat` (synthesised, chopped),
  `reese` (square + detune + sub, resonant 24 dB LP), `lead_pwm`, `lead_fm`,
  `pad`, `stab`.
- **Improved acid** (`acid.txt`): per-step `accents`, high-pass, a resonant
  `equalizer` peak, plus an F-based 303 line with octave skips/slides.
- Arrangement: intro -> drop1 -> build -> breakdown -> drop2 -> breakdown2 -> main
  -> final -> fade.
- Builds to `output/techno_v4.wav` (-12.9 LUFS, peak -0.9 dBFS, 240 s).

## Optional next

- Render a video for the Basement track (the girl loop currently matches the
  hardgroove vibe; the jungle track may want a different source clip).
- Ear-check the Basement mix and rebalance boosts/levels.
- Re-render the hardgroove video against the latest mastered audio.

## Known issues

- The `edge` look needs the RVM model; the `pollock` look does not.
