# fftechno - status

A four-minute hardgroove techno track (all sound synthesized by ffmpeg) plus a
black-and-white dancing-girl music video, driven by markdown.

## Done

- `song.md` - arrangement + mix: `bpm/bars/fade_bars`, `sidechain_key`, `low_bus`,
  and the tables **Stems, Boosts, Sections, Pan, Effects, Levels**.
- `sounds.md` + `templates/` - all 12 instruments parameterised (kick, clap, hat,
  ohat, conga, bongo, rim, shaker, bass, acid, growl, beeps) via `{{key}}` and
  `{{if_steps(seq; grid; default)}}`.
- **Lossless port**: the generated `filters/*.txt` reproduce the original graphs
  (<= -213 dB, float noise).
- Drum rhythm lives inside the instrument (`gates` / `pitches`), so hit tails are
  preserved; no mix-level gate.
- Master: two-pass linear loudnorm -> -13.0 LUFS / -1.0 dBFS.
- Build lock prevents overlapping builds from corrupting stems.
- **Conga**: `templates/conga.txt` (tuned hand drum + slap) replaces the loud tom
  `perc` stem; lower boost.
- **Voice**: ffmpeg's built-in `flite` (`slt`) - no external espeak-ng.
- **Dancing-girl video**: `fftechno/girl.py` crops 2.0-5.0 s (7 beats) of the
  `ascii/` clip, mattes the girl with RVM (`fftechno/matte.py`, onnxruntime,
  largest-component keep), edge-detects (white on black) and loops it on the beat
  grid. Emits `girl_loop.mp4` + `girl_frames.npy`; `visualizer.vpy` uses it as the
  main visual (subtle Berlin overlay, kick punch).
- **ffmpeg 9**: filtergraphs read with `-/filter_complex FILE`.
- **Non-clobbering outputs**: `config.unique_path` writes `_v2`/`_v3` names.
- Docs: `README.md`, `SPEC.md`, `LICENSE.md`, `TODO.md`.

## Optional next

- Re-render the video against the latest mastered audio (video embeds the WAV).
- Expose more parameters in markdown: growl grain timings, vox phrases/placements.
- Optional `Patterns` table in `song.md` as a friendlier front-end to `gates`.

## Known issues

- RVM keeps any large person in frame; `largest_component` drops the crowd except
  where a bystander touches the girl (a few frames near 4.5 s).
