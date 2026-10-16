# fftechno - status

Songs under `songs/` (all sound synthesized by ffmpeg), driven by markdown:
**basement** (155 BPM jungle techno), **hardgroove** (140 BPM), **minimal**
(100 BPM, 7 stems, 1920x1080 `photo` video) and **triphop** (84 BPM, audio only).
**triphop_beat** is an 8-bar scratch at 88 BPM. A folder is the song. There is
no song subclass.

## Done

### Engine + tooling
- Markdown control surfaces: `song.md` (arrangement + mix) and `sounds.md`
  (instruments), rendered through `templates/` via `{{key}}` and
  `{{if_steps(seq; grid; default)}}`.
- Master: two-pass linear loudnorm -> -13.0 LUFS / -1.0 dBFS; optional
  **`--safe`** ear-protection limiter (off by default).
- Build lock; non-clobbering outputs (`config.unique_path` -> `_v2`/`_v3`).
- **ffmpeg 9**: filtergraphs read with `-/filter_complex FILE`.
- Voice: local neural TTS - Kitten TTS (default) / Piper - short phrases
  from `songs/<song>/vocals.md`, which also drive the on-screen lyrics.
- Video (`fftechno/girl.py`, `matte.py`, `visualizer.vpy`): beat-locked dancing-girl
  loop with `--look edge|pollock|outline|photo` and `--mode
  reset|trail|build`. The **outline** look shows only the silhouette contour
  (no face interior, crowd removed) with the **blue hair chroma-keyed**, cuts
  random stills in **on the beat**, and burns the **lyrics** in at the vocal
  times; the shader preserves chroma.

### Track 1 - "hardgroove" (`songs/hardgroove/`)
- 140 BPM, 140 bars; 12 instruments (kick, clap, hat, ohat, conga, bongo, rim,
  shaker, bass, acid, growl, beeps); the `edge` video look.

### Track 2 - "Basement" jungle techno (`songs/basement/`)
- **155 BPM, 155 bars = 4:00**, sidechain on kick, `reese` low bus.
- **16 instruments**: kick, snare, snarefill, clap, hat, ohat, ride, crash,
  breakbeat, conga, shaker, reese, acid, lead_pwm, lead_fm, pad, stab - plus the
  **vox** stem (Kitten TTS / Piper, short phrases with matching on-screen lyrics).
- New templates: `snare`, `ride`, `crash`, `breakbeat` (synthesised, chopped),
  `reese` (square + detune + sub, resonant 24 dB LP), `lead_pwm`, `lead_fm`,
  `pad`, `stab`.
- **Improved acid** (`acid.txt`): per-step `accents`, high-pass, a resonant
  `equalizer` peak, plus an F-based 303 line with octave skips/slides.
- Arrangement: intro -> drop1 -> build -> breakdown -> drop2 -> breakdown2 -> main
  -> final -> fade.
- Builds to `output/basement/techno.wav` (-12.9 LUFS, peak -0.9 dBFS, 240 s).

### Track 3 - "minimal" (`songs/minimal/`)
- **100 BPM, 75 bars = 3:00**; Robert-Hood-style. A dry **4-on-4 kick that never
  drops**; **7 stems**: kick, hat (`hat_step`), ohat (`ohat_dyn`), snare, rim, bass,
  and one `blow` stem.
- Closed hats on the 8ths, open hats on the offbeats with per-hit dynamism (decay
  varies 25x, accents ~7 dB - deterministic, never a fixed bar loop).
- Snare on the backbeat and rim on the "a"; both appear late / drop out to keep the
  long form interesting while the kick stays constant.
- Bass: one root note every 16th under a **resonant low-pass**
  (`lowpass=f=320:t=q:w=1.4`); `bass.txt` gained `lp_q` (Hardgroove passes
  `lp_q=0.707` and is byte-identical).
- Builds to `output/minimal/techno.wav` (-13.3 LUFS, peak -0.9 dBFS, 180 s).
- **Video** (`songs/minimal/video.md`): the still photo (`look: photo`, centred on
  black, watermark cropped) plus the `squares, grain` effect chain. Six concentric
  white outline squares - one per instrument, largest outermost - each driving one
  parameter (kick size, bass drift, hat thickness, ohat rotation, snare knock, rim
  flash) and drawn **only while its instrument is audible**. Renders to
  `output/minimal/techno_visualizer.mp4` (1920x1080, 180 s).

## Done - Track 4 "trip hop" (`songs/triphop/`)

Instrumental, audio only. **84 BPM, 84 bars = 4:00.** D minor, one 8-bar phrase.
The master on disk is `output/triphop/techno_v4.wav`.

- **Stems:** kick (`boom.txt`), brk (`break_sp.txt`), roll, sub, ep, strings, bell,
  stab (`dubstab.txt`), horn, rise, vinyl. Side-chain key is `kick`. Low bus is `sub`.
- **`songs/triphop_beat/`** is an 8-bar scratch at **88 BPM** (~21.8 s): `kick_trip`,
  `break_synth`, `bass_gate`. It is not the 4-minute song. Its break swings at
  phase 0.14 of a step. The shipped break (`break_sp`) swings at 0.22.
- An earlier plan used 88 BPM, a sax lead and a Rhodes piano. That plan is not the
  shipped song. `sax.txt` and `rhodes.txt` stay in `templates/` as examples.
- `bar`, `step`, `beat` and `dur` come from `song.md`. Do not copy them into
  `sounds.md`.

### Docs - `AEVAL_TUTORIAL.md` (done)

A from-scratch tutorial on ffmpeg as a synthesizer: the `aevalsrc`/`aeval`
primitives, the oscillator/envelope/modulation library, how each instrument is
built, step sequencing and the `if_steps` ladder, note length vs grid, swing as a
pairwise time warp, deterministic randomness (`random(idx)`, `st`/`ld`, per-step
hashes), the effect mapping to DAW plugins, a DAW/Electribe comparison, and the
"no MIDI, not realtime" answer. Every runnable example was executed against
ffmpeg 9.0.2 (see the doc's preamble). Linked from README + SPEC.

## Optional next

- Decide whether to bring the `vox` tick back: `songs/minimal/vocals.md` is parked,
  so it needs `vox` in the Stems table plus a `Levels` row (2.5 measured about
  3.6 dB under the kick), and the ticks would then also be the on-screen lyric.
- **Leading-silence trim for the other songs.** `trim_lead` is implemented and used
  by `minimal`; `basement` and `hardgroove` do not set it, so their phrases still
  land ~0.65 s after their `vocals.md` times (and so do their on-screen lyrics).
  Turning it on for them fixes the sync but moves those vocals earlier.
- Ear-check the `minimal` mix (snare/rim/hat balance, `lp_bass` 320 vs higher) and
  rebalance the `Boosts`/`Sections` if needed.
- Eye-check the `minimal` video: the `halves` composition and `focus` (0.393), the
  ring's `swell`, and `thickness` (2).
- **Per-stem FX in the mixer ("Option B"):** add an optional `Sends` table to
  `song.md` so an individual stem can be sent to the project's convolution reverb
  (`logs/ir.wav`) and a real delay line, instead of baking effects into a template.
- **Swing:** verified expressible as a pairwise time-warp in `aevalsrc` (measured
  2:1 onsets). A clean version needs `if_steps` to accept an inline grid expression,
  plus one swing-aware template.
- More effects for the chain (e.g. scanlines, chromatic aberration, a grid, orbit
  paths) - each is one class in `fftechno/effects.py`.

## Done - `minimal` video (reactive squares)

Built as the first **effect chain** (`look: photo` + `effects: squares, grain`); see
SPEC.md 12.5. Notes kept for reference:

- The chain lives in `fftechno/effects.py`: **paint** effects (numpy, per frame) and
  **shader** effects (GLSL, spliced into the vs-placebo shader). Selected by
  `effects: a, b` in `video.md` or `--fx a,b`; knobs share the `## Parameters` table.
- Shapes: concentric white outlines, one per instrument, largest outermost; the rim
  shot is a **ring at the centre** (`circles: rim`), the others squares. A shape is
  shown only while its instrument is audible and **hidden, never dimmed**; the drawn
  level is `level` (1.0 = pure white). A size cap keeps a square from outgrowing the
  frame (its edges would otherwise clip into stray full-width lines).
- Output is **1920x1080**. `minimal` sets no `size:` line. The photo is
  `fill`-framed (cover + centre-crop), so there is no black gap. The size is per song
  and drives the picture frame, the strip rows, the shader coordinates and the
  preview (1280x720 when the frame is landscape).
- The previously hard-coded shader became four selectable effects (`kick_flash`,
  `vignette`, `grain`, `kick_glitch`) = the built-in default chain, so songs that
  name no effects render as before. Verified by frame hash: `basement` and
  `hardgroove` frames identical (the `edge`/stack path has pre-existing ±4/255 grain
  jitter between runs; the sprite path is fully deterministic).
- Per-instrument envelopes are the *gain-applied* stems (`logs/fx/<stem>.wav`,
  `arrangement.gain_expr`), so the visuals follow the arrangement. Verified
  headlessly: square presence per bar matches `song.md` (kick only at bar 2;
  +bass/hats at 16; snare at 32; rim at 48; snare fading out at 60).
- `girl.py` no longer requires the RVM matte for sprite looks, and a still source
  skips the crop seek (an image has no timeline).

## Done - `minimal` tick lyric and framing

- **Tick lyric.** `songs/minimal/vocals.md` places a "tick" on each of the four kicks
  of the opening bar (0.0/0.6/1.2/1.8 s) and `trim_lead: 1` strips the leading silence
  the TTS pads onto a phrase, so the ticks land **on** the kicks instead of late (the
  engine is now **`flite`** - ffmpeg's own built-in TTS, voice `slt` - measured onsets
  0.005/0.605/1.205/1.805 s; Kitten was 0.02/0.62/1.22/1.82 s and did not sound
  good). **Parked:** the track is instrumental for now, so `vox` is out of `song.md`'s
  Stems table, the lines stay in `vocals.md` for later, and `audio.build` deletes
  `lyrics.json` (no on-screen lyric).
- **Intro reduced.** The 38 s bare-kick intro is now **one bar** (4 kicks + 4 ticks);
  the later sections moved 15 bars earlier and the last two stretch, so the track is
  still 75 bars = 3:00. (The alternative - letting it become 60 bars = 2:24 - was not
  taken; say the word and it is a two-line change.)
- **Nose at the circle's centre.** `photo` gained `focus` - the vertical fraction of
  the image that must land at the middle of the frame (measured 0.393 for this photo,
  via the render - the blue-hair mask was useless here because the alley's neon is
  blue too). The cropped window is symmetric about it, so the framing stays as wide
  as the aspect allows.
- **Face inside the ring.** `squares` gained `halves` (explicit sizes in instrument
  order) so the composition can be designed; the current ladder is
  `220.5|190|68|98.5|159.5|129` - evenly spaced 30.5 apart (so no square sits in a
  wide gap), with the snare and hat swapped and everything 5% larger, and the ring
  (129) enclosing the face.
- **Instrumental for now.** The `vox` tick was removed from the mix: `vox` is out of
  `song.md`'s Stems, `vocals.md` keeps the lines parked, and `audio.build` now
  deletes a stale `lyrics.json` when there is no vocal stem (otherwise the video
  would still draw the on-screen "TICK"). Bar 0 is a bare-kick bar again.
- **Picture shifted.** `photo` gained `shift_x`/`shift_y` (output pixels, positive =
  right/down), implemented by moving the crop window the other way. Set to -25/-25
  (left and up), verified numerically to move the content exactly 25 px.
- **`flite` TTS engine.** `vox.py` gained ffmpeg's built-in TTS (libflite voices
  `slt`, `kal`, `kal16`, `rms`, `awb`) as a third engine next to Kitten and Piper -
  no model files, no network; `--tts flite` on the CLI.
- **One blow stem.** `templates/blow.txt` repeats a filtered-noise puff every
  `period` seconds. `minimal` uses one stem, panned right: 13 puffs of ~0.26 s from
  the 2:00 mark to about 177.6 s. The earlier five-stem version is not the song.
- **`Levels` stems honour the `Pan` table** (they used to be folded to mono centre).
  Basement/hardgroove levels halved to compensate (vox 6.0 -> 3.0 and 1.5 -> 0.75,
  beeps 1.0 -> 0.5); verified: same peak and RMS to <0.001 dB, bit-identical for 239
  of 240 s.
- **Squares 25% bigger** (`275.625|237.5|85|123.125|199.375|161.25`) with the kick
  moved from *size* to *thickness*: the outermost square already reaches the frame, so
  growing it would just clamp. The ring still pings by growing.
- **Re-cut for the new still + horizontal frame.** The second Gemini still
  (`...51i77351i77351i7.png`, 2752x1536) in a 1920x1080 frame: `size:` dropped, `focus`
  re-measured to 0.324 (it zooms so her nose is at the ring's centre - and a wider
  `focus` *shrinks* what you see, since the symmetric window is `2*f*ih` tall), and the
  ladder re-spaced to `245|217|133|161|189|105` (even 28 px gaps, the ring at 105
  enclosing her face). `crop_right` was added for the watermark (x 0.88-0.925,
  y 0.843-0.857) but the zoom now excludes it.
- **Blow series.** `blow.txt` gained `period`: a stem fires a puff every `period`
  seconds from `at`. `minimal` uses **one blow stem panned right** (`0.20/0.80`):
  **13 puffs of ~0.26 s**, every two bars from 120.0 s to 177.6 s (repeated to the end).
  It is an *arranged* stem (constant `1.00`) so the last puffs fade with the outro, and
  `skip: vox|blow` keeps it out of the squares.
- **Fade fix.** The final section is now exactly `fade_bars` long (`68-75`, `49-68`
  before it): previously `65-75` with `fade_bars: 7` meant the fade completed at bar 72
  and the last ~7 s were silent, which also swallowed the closing puffs.
- **Frame nudge.** `shift_x: -50`, `shift_y: -60` (the subject moves left and up by that
  many output pixels).
- **Ping-pong delay on the blow.** Built into `templates/blow.txt` as a stereo stem
  (dry + two `aecho` tap sets, hard left and hard right) and passed through the mix with
  the new `Pan` `keep` mode. Verified: dry R -7.9 dB, taps L +3.3, R -9.9, L +0.8.
- **`swap` command** (`python -m fftechno swap --song S`): replaces an MP4's audio with
  the current master with the video **copied** - no re-render. Used for the blow change;
  the frames are the ones already rendered.
- **Two bugs found on the way:** `audio.render_stems` now cuts each stem at the song's
  duration (the blow's delay tail was stretching the master to 182.25 s), and
  `cli._latest()`'s glob matched `techno_visualizer_720p.mp4` when asked for
  `techno_visualizer.mp4` (so `boost`/`swap` could hit the wrong file).
- Rebuilt: `techno.wav` (-13.2 LUFS, 180.000 s) and the video.

## Known issues

- The `edge` look needs the RVM model; the `pollock` look does not.
