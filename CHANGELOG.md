# Changelog

## Unreleased
- **Sample-based songs.** A song can make sound from audio files instead of `aevalsrc`
  oscillators. `samples/manifest.md` (tracked) lists every sample with URL and licence;
  `python -m fftechno samples` downloads and normalises them to 48 kHz PCM
  (`fftechno/samples.py`; the wavs are gitignored). A `## Samplers` table in `sounds.md`
  (`name | sample | params`) becomes a generated graph (`fftechno/sampler.py`) that reads
  the file with `amovie`, fans it with `asplit` and places each hit with an absolute
  `adelay`, so it flows through the normal stems -> mix -> master pipeline. `proc.run`
  gained a `cwd`, and `render_stems` runs ffmpeg from the repo root so the repo-relative
  `samples/...` path resolves. New song `triphop_samples` (88 BPM, 8 bars): the TR-909 SP
  kit over a slowed Amen break. Additive - existing songs' filters are unchanged.
- **Clocks come from `song.md`.** `bar`, `step`, `beat` and `dur` are computed from
  `bpm` and `bars` when `sounds.md` is rendered. A copy of those four names in
  `sounds.md` fails the build. Other scalars may use `{{bar}}`, `{{step}}` and
  `{{beat}}`. The 4-minute trip-hop master was not rebuilt for this.
- **One markdown reader.** `fftechno/md.py` reads tables and scalars for `song.md`,
  `sounds.md`, `vocals.md` and `video.md`.
- **A song is a folder.** `load(name)` returns `Song(name)`. The empty song
  subclasses and the `SONGS` registry are gone.
- **Arrangement check.** Sections start at bar 0, meet with no gap, and end at
  `bars`. Every stem is in Sections or Levels. Every arranged stem has a Boost.
  A Levels-only stem (the voice) stays out of Sections.
- Removed unused `Song.look_param`, `PaintCtx.white`, and `GIRL_FRAME_W` /
  `GIRL_FRAME_H`.
- **Pluggable video effects.** The picture is now a **source** (`Look`) plus an
  ordered **effect chain** (`fftechno/effects.py`): paint-tier effects draw per frame
  in numpy, shader-tier effects are spliced into the vs-placebo GLSL. Chosen per song
  with `effects: a, b` in `video.md` (or `--fx a,b`); knobs share the
  `## Parameters` table. Shipped: `squares` (new) plus `grain`, `vignette`,
  `kick_flash`, `kick_glitch` - the previously hard-coded shader, now selectable.
  Songs that name no effects keep the old chain and render unchanged (verified by
  frame hash).
- **New `photo` source** (`looks.py`): a still image as the picture, full colour,
  centred on black, with an optional `crop_bottom` (used to crop a watermark). Still
  sources skip the crop seek, and sprite looks no longer need the RVM matte.
- **Instrument reactivity.** `video.py` bakes each instrument the chain needs into
  `logs/fx/<stem>.wav` with its `Sections` automation applied, so a visual follows
  the arrangement (the snare's square is absent while its section gain is `0.00`).
- **`blow` - a candle puff of filtered noise** (`templates/blow.txt`): noise through a
  high-pass, a low-pass and a resonant peak, with a rise-and-decay envelope. It takes a
  `period`, so a stem fires a puff every `period` seconds from `at` - a graph with its
  own timing instead of a step pattern. `minimal` uses a **single blow stem panned right**
  (`stereo 0.20/0.80`): **13 puffs of ~0.26 s**, one every two bars from the 2:00 mark to
  177.6 s, i.e. repeated to the end of the track. It is an *arranged* stem held at `1.00`
  (not `Levels`) so the last puffs fade with the outro, and `skip: vox|blow` keeps it out
  of the `squares` pattern.
- **`swap` command.** `python -m fftechno swap --song S` replaces an MP4's audio with
  the current master, **copying the video stream** - the way to apply an audio-only
  change without re-rendering frames (`boost` re-encodes the audio through a limiter,
  which would squash the master). Also fixed: `_latest()`'s glob matched
  `techno_visualizer_720p.mp4` when asked for `techno_visualizer.mp4`, so `boost`/
  `swap` could target the wrong file - the match is now anchored.
- **Ping-pong delay on the blow.** `templates/blow.txt` now builds a stereo ping-pong
  in the stem's own graph: the dry puff plus two `aecho` tap sets, one hard left and one
  hard right (`dry_l/r`, `ltaps/ldec`, `rtaps/rdec`), so the repeats alternate sides -
  verified in the mix: dry R -7.9 dB, taps L +3.3, R -9.9, L +0.8.
- **`Pan` `keep` mode.** A stem that is already stereo (an effect built into its own
  graph) is passed through instead of folded to a point.
- **`swap` command.** `python -m fftechno swap --song S` replaces an MP4's audio with the
  current master, **copying the video** - the way to apply an audio-only change without
  re-rendering frames. (The `minimal` master video and preview were updated this way;
  frames untouched.) `boost` remains the "re-encode the audio at a gain" path.
- **Stems are cut to the song's duration** (`audio.render_stems`): a graph that adds a
  tail (the blow's delay) used to stretch the stem past the song and with it the whole
  mix - the master came out 182.25 s. A no-op for the tail-free templates.
- **`_latest()` anchored match.** Its glob matched `techno_visualizer_720p.mp4` when
  asked for `techno_visualizer.mp4`, so `boost`/`swap` could silently target the wrong
  file; the match is now exactly `name[_vN].ext`.
- **Fade structure.** `minimal`'s final section was 10 bars with `fade_bars: 7`, so the
  fade completed at bar 72 and the last ~7 s of the track were silent (the last two puffs
  were inaudible). The final section is now `fade_bars` long (`68-75`, with `49-68`
  before it), so the fade ends exactly with the track. Worth remembering for any song:
  the last `Sections` row should be `fade_bars` long.
- **`minimal` re-cut for the new 16:9 still and a horizontal frame.** `size:` is dropped
  (1920x1080) and the source is `Gemini_Generated_Image_51i77351i77351i7.png`;
  `focus: 0.324` zooms so the subject's nose lands at the centre of the ring, and the
  `halves` ladder was re-spaced for the new framing (`245|217|133|161|189|105`, ring
  enclosing her face, even 28 px gaps).
- **`crop_right`** (`photo`): trims a fraction off the right. The new still's watermark
  sits at x 0.88-0.925 / y 0.843-0.857, so a bottom crop would have had to eat 16% of the
  frame; the `focus` zoom now excludes it, so the knob ships unused.
- **`Levels` stems now honour the `Pan` table.** They used to be folded to mono
  centre, which made the table meaningless for a non-arranged stem. Basement's and
  hardgroove's levels were halved to compensate (6.0 -> 3.0, 1.5 -> 0.75, beeps
  1.0 -> 0.5); the re-mixed `mix_pre.wav` has the same peak and RMS to <0.001 dB and
  is bit-identical for 239 of 240 seconds (the residue is the fold's rounding through
  the side-chain and bus compressor, <= 0.0118 in the fade-out tail).
- **Bigger squares, kick on thickness** (vertical cut). The `halves` ladder grew 25%
  (`275.625|237.5|85|123.125|199.375|161.25`; re-spaced again for the horizontal re-cut
  below). The outermost square was then wider than
  the frame can grow into, so the kick no longer drives *size* (it would simply clamp
  at the frame) - it pulses by **thickening** its line instead, and the ring still
  pings by growing.
- **`minimal` tick count-in (parked).** `songs/minimal/vocals.md` places a "tick" on
  each kick of the opening bar, synced to the kick: `trim_lead: 1` strips the leading
  silence the TTS pads on (without it every phrase sounds that much late). It is
  **not in the mix at the moment** - `minimal` is instrumental, so `vox` is out of its
  Stems table and `audio.build` deletes the stale `lyrics.json` (otherwise the video
  would still draw the on-screen "TICK"). Add `vox` back to the Stems table (plus a
  `Levels` row) to bring the ticks back.
- **`flite` TTS engine.** `vox.py` can now use **FFmpeg's own built-in TTS**
  (libflite: `slt`, `kal`, `kal16`, `rms`, `awb`) - no model files and no network,
  so the voice is as self-contained as the rest of the audio path.
- **Framing `focus` and `shift_x`/`shift_y`.** `photo` can name the vertical fraction
  of the image that must land in the middle of the frame (the nose at `0.393` for
  `minimal`), so the pattern centred on the frame is centred on the subject's face,
  and can nudge the subject within the frame in output pixels (verified: 25 px moves
  exactly 25 px). `squares` gained `halves` (explicit sizes per instrument, in order)
  to design the composition.
- **`songs/minimal/video.md`** - the photo plus `squares, grain`: white outlines, one
  per instrument, that vibrate with the track (concentric squares, and a **ring** for
  the rim shot at the centre). Output is **vertical 1080x1920** (9:16) with the photo
  `fill`-framed, so there are no black bars. `python -m fftechno video --song minimal`.
- **Vertical video support.** The output size is per song (`size: WxH` in `video.md`,
  default 1920x1080): the picture-data frame, the audio data strip rows, the shader's
  strip coordinates and the preview (720x1280 when vertical) all derive from it.
- **`photo` framing.** `framing: fit` (letterbox, the default) or `fill` (cover +
  centre-crop); `crop_bottom` trims a fraction off the bottom (a watermark).
- **`squares` presence is on/off.** A shape is drawn pure white while its instrument
  is audible and hidden when muted - never dimmed. `circles` selects which
  instruments are rings, and a size cap keeps a square from being clipped by the frame.
- **`songs/minimal/`** - a minimal, meditative track in the Robert Hood mould:
  100 BPM, 75 bars = 3:00. A dry 4-on-4 kick that **never drops**, 8th closed hats,
  offbeat open hats with per-hit dynamism, a backbeat snare, rim shots, and a
  one-note bass under a resonant low-pass. No vocals, no video.
- **Revision after first listen:** the kick lost its `aecho` room and the beatless
  "breaths" (4-on-4 throughout); the random golden-ratio hat was replaced by a
  steady gated one (`hat_step.txt`); snare, rim and `ohat_dyn.txt` were added.
- **Three new templates** - `hat_step.txt` (gated noise hat with a `vel` accent
  list), `ohat_dyn.txt` (open hat whose decay *and* velocity vary per hit) and
  `kick_verb.txt` / `hat_rand.txt` (kept as available variants). `bass.txt` gained
  `lp_q`, making its low-pass resonant; Hardgroove passes `lp_q=0.707` and renders
  **byte-identical** to before.
- `fftechno/song.py`: `Minimal` subclass registered.
- Docs: `SPEC.md` (template variants, tracks, extension guide, inventory) and
  `README.md` (Tracks table, optional `vocals.md`/`video.md`) refreshed.

## v0.2

**Architecture**
- **Songs are folders.** All track-specific data lives in
  `songs/<name>/` (`song.md`, `sounds.md`, `vocals.md`, `video.md`); the code has
  no hardcoded track values. Both tracks ship: Basement and Hardgroove.
- **`fftechno/song.py`** - an abstract `Song` (paths, derived timing, vocals,
  video) with thin per-song subclasses.
- **`fftechno/looks.py`** - the video styles (`edge`, `pollock`, `outline`) are
  `Look` strategies; `girl.py` is a generic pipeline.
- CLI: every command takes `--song <name>`; output goes to `output/<song>/` and
  filter graphs to `filters/<song>/`.
- Linting/formatting: **black + ruff + pyflakes** (see `Taskfile.yml`, `task lint`).

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
