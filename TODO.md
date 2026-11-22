# fftechno - open work

`README.md` and `SPEC.md` are the authoritative docs. This file lists only work that
is still open.

## Verification

- [ ] **Full nine-song audio audit.** Run
  `python -m fftechno audio --song S --out out2` for every folder under `songs/`
  and record each exit code, duration and loudness. The last run completed
  `basement` (240.000 s) and `triphop_beat` (21.818 s); `hardgroove` was partial and
  the rest were skipped. `out2/` is gitignored, so recreate it when resuming.
  `basement` and `hardgroove` need the Kitten TTS model; the other seven songs are
  instrumental or sample-only.
- [ ] **Remove or archive the stale worktree.** `.worktrees/aeval` (branch
  `aeval-split`) is separate from the main build and needs explicit approval before
  removal.

## Engine and mixer

- [ ] **Stem cache.** Skip re-rendering a stem when its graph and inputs have not
  changed. A 4-minute stem at 192 kHz is ~46 million samples and there is currently
  no cache, so every build re-renders everything.
- [ ] **Per-stem `Sends` table.** Add an optional table to `song.md` so an
  individual stem can use the project convolution reverb (`logs/ir.wav`) and a real
  delay line instead of baking effects into a template. This also covers the psych
  dry-kick/dry-bass wash and a dedicated drum room/plate send.
- [ ] **Swing.** A pairwise time-warp in `aevalsrc` is measured at 2:1 onsets. A
  clean implementation needs `if_steps` to accept an inline grid expression plus one
  swing-aware template.
- [ ] **Missing-sample errors.** Make the `## Samplers` graph fail with the exact
  `sounds.md` row when a file is absent, instead of a downstream filter error
  (`rim`/`snare-short` are fetched but unused today).
- [ ] **More visual effects.** Add options such as scanlines, chromatic aberration,
  a grid or orbit paths; each is one class in `fftechno/effects.py`.

## Song polish

- [ ] **`minimal` count-in.** Decide whether to bring the parked `vox` tick back:
  it needs `vox` in the Stems table and a `Levels` row (measured about 3.6 dB under
  the kick), and the ticks would double as the on-screen lyric.
- [ ] **Vocal sync on `basement` and `hardgroove`.** `trim_lead` is implemented and
  used by `minimal`, but these two songs do not set it, so phrases land about 0.65 s
  after their `vocals.md` times (and so do the lyrics).
- [ ] **`minimal` mix ear-check.** Check the snare/rim/hat balance and `lp_bass`
  (320 vs higher), then rebalance `Boosts`/`Sections` if needed.
- [ ] **`minimal` video eye-check.** Check the `halves` composition, `focus` (0.324),
  the ring's `swell`, and `thickness` (2).
- [ ] **`psych` lead.** Add a vocal (spoken/TTS) or a synth lead if the instrumental
  needs a hook.
- [ ] **`stoner_samples` colour.** Try a sampled organ or tambourine for the chorus.
- [ ] **Longer-form variation.** Add a real bridge instead of relying only on
  section gains (most useful for the sample-based and rock tracks).
- [ ] **Keep the Amen break stereo.** The sampler currently folds every source to
  mono; preserving the stereo Amen would restore its width.