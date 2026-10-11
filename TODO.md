# fftechno - status

A four-minute hardgroove techno track (all sound synthesized by ffmpeg) plus a
black-and-white ASCII video, driven by markdown.

## Done

- `song.md` - arrangement + mix: `bpm/bars/fade_bars`, `sidechain_key`, `low_bus`,
  and the tables **Stems, Boosts, Sections, Pan, Effects, Levels**.
- `sounds.md` + `templates/` - all 12 instruments parameterised (kick, clap, hat,
  ohat, perc, bongo, rim, shaker, bass, acid, growl, beeps) via `{{key}}` and
  `{{if_steps(seq; grid; default)}}`.
- **Lossless port**: the generated `filters/*.txt` reproduce the original graphs
  (<= -213 dB, float noise); `output/techno.wav` is byte-identical to the reference.
- Drum rhythm lives inside the instrument (`gates` / `pitches`), so hit tails are
  preserved; no mix-level gate.
- Master: two-pass linear loudnorm -> -13.0 LUFS / -1.0 dBFS.
- Build lock prevents overlapping builds from corrupting stems.
- Video: `visualizer.vpy` (VapourSynth + GLSL, ASCII + B/W overlay).
- Docs: `README.md` (beginner/musician), `SPEC.md` (technical), `LICENSE.md`.

## Optional next

- Expose more parameters in markdown: growl grain timings, vox phrases/placements.
- Optional `Patterns` table in `song.md` as a friendlier front-end to `gates`.
- Re-render the video against the restored audio.

## Known issues

- None outstanding.
