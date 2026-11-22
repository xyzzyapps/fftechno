# fftechno - status

Songs under `songs/`, driven by markdown: **basement** (155 BPM jungle techno),
**hardgroove** (140 BPM), **minimal** (100 BPM, 7 stems, 1920x1080 `photo` video),
**triphop** (84 BPM, audio only), **triphop_beat** (88 BPM, 8-bar scratch) and
**triphop_samples** (84 BPM, 80 bars = 3:48.6, four elements: Amen break, sub,
electric piano, vinyl; delivered cut 3:42.9). **psych**, **stoner** and
**stoner_samples** are the rock tracks. A folder is the song. There is no song
subclass.

This file is a chronological log. Earlier entries may describe superseded
versions; the summary above, `README.md` and `SPEC.md` are authoritative.

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

## Open - full song build audit

- Run `python -m fftechno audio --song S --out out2` for all nine songs and record
  each duration, loudness and exit code. This was stopped at the user's request after
  `basement` (complete, 240 s) and `triphop_beat` (complete, 21.818 s); `hardgroove`
  was partial. `out2/` is gitignored and was removed/stopped, so recreate it when
  resuming.
- `hardgroove` and `basement` need the Kitten TTS model; the other seven are
  instrumental or sample-only.

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

## Done - first sample-based trip-hop beat (`songs/triphop_samples/`, superseded)

The first **sample-based** song: real audio files instead of `aevalsrc` oscillators.
This 8-bar, 88 BPM scratch was replaced by the full four-element track below.

- **Samples store** (`samples/manifest.md`, tracked; the wavs are gitignored):
  `python -m fftechno samples` downloads and normalises each file to 48 kHz PCM
  (`fftechno/samples.py`). Sets: `triphop_kit` (TR-909 SP, oramics/sampled) and
  `breaks/amen.wav` (schollz/amen, MIT).
- **Sampler instruments** (`fftechno/sampler.py`): a `## Samplers` table in
  `sounds.md` (`name | sample | params`). `synth.generate` writes a graph that reads
  the file with `amovie`, fans it out with `asplit` and places each hit with an
  **absolute** `adelay` (`pat` = per-bar 16th pattern, `hits` = absolute steps,
  `rate` varispeed, `trim`, `vel`, `gain`). `render_stems` now runs ffmpeg from the
  repo root so the repo-relative `samples/...` path resolves (`proc.run(cwd=...)`).
- **New song** `songs/triphop_samples/`: 88 BPM, 8 bars. TR-909 SP kit over the Amen
  break slowed to `rate=0.81`. Onsets land on the grid (+/- 0.3 ms); master is
  21.818 s, -13.1 LUFS, -1.0 dBTP.
- **Additive verified:** `synth --song minimal` and `--song basement` produce no diff
  (existing `filters/` unchanged). Docs: README + SPEC 21.
- **Early placement:** this first version placed every hit with an absolute `adelay`
  (one chain per hit). The full track below uses the `pat` + `aloop` path instead.

### Done - full sample trip hop (`triphop_samples`)

User was unhappy with the earlier results; the repo had also moved on (a committed
synth `triphop` at 84 BPM + the sample route). A stale-architecture rewrite had
clobbered `songs/triphop/`; **restored from HEAD** and deleted the redundant
`th_*` templates it added.

- **`songs/triphop_samples/` is now a full track**: 84 BPM, 84 bars = 4:00, D minor.
  Drums are real samples - the **Amen** varispeeded **136 -> 84** (`rate=0.617647`)
  and trimmed to exactly two bars so its backbeat lands on the grid (the old
  `rate=0.81` did not fit the bar), high-passed to sit in the midrange; the TR-909 SP
  kit supplies kick / snare / hats, the snare given a dark plate tail via per-hit
  `fx` `aecho`.
- Harmony / hook / dust are the synth voices reused from `songs/triphop`
  (`sub`, `ep`, `strings`, `bell`, `horn`, `dubstab`, `vinyl`) on the same 8-bar
  Dm9-Gm9-Bbmaj7-A7 loop; 12 stems, sparse half-time arrangement, low global reverb.
- All 12 filter graphs dry-run clean; built `techno_v3.wav` (240 s, -12.9 LUFS).
- **Rebalanced** after measuring stems: the snare peaked ~10 dB under the kick and
  the hats/hook were buried while the sub was hottest - wrong for the genre. Boosts
  now snare 3.2 / hat 1.8 / brk 1.3 / bell 1.7, sub 1.1 / kick 1.6. Re-mixed (stems
  unchanged) -> **`techno_v4.wav`**, -13.0 LUFS / -1.1 dBTP.
- Break verified: loops seamlessly every 2 bars, backbeat near 2 & 4 (the kit snare
  supplies the precise grid on top).
- **Arrangement made coherent** (user: "elements present but arrangement
  incoherent"): the old boundaries (40/64/72/76/84) cut across the 8-bar chord
  phrase and layers toggled unannounced. Now **80 bars = 10 x 8-bar phrases**, every
  boundary on a phrase; added self-timed `roll` (rising snare fill, last 2 beats of
  each phrase) + `rise` (reversed swell) as transition markers; clear arc
  intro -> pulse -> groove -> hook -> breakdown -> drop -> peak -> dub space ->
  final -> outro bookend. Verified roll fires at bars 7.5/15.5/23.5/... .
  -> **`techno_v5.wav`**, 228.6 s, -13.0 LUFS / -1.1 dBTP.
- **New arrangement, same elements** (user request): the **break loop is now the
  spine** - it opens the track alone with vinyl (crate-dig), stays present until the
  outro; sub/kick lock in at 8, chords at 16, hook at 24; a **one-bar full stop**
  (bar 39, dust only) sets up the drop at 40; two dub breakdowns; outro returns to
  the opening loop. Verified the stop: bars 36-39 -12 dB RMS, 39-40 -29 dB, 40-43
  -11 dB. Re-mixed from existing stems -> **`techno_v6.wav`**, -13.0 LUFS / -1.1 dBTP.
- **User feedback: opening break good; the kit layered on top bad; bass + synth
  good.** The break already carries kick/snare/hats, so the added 909 kit
  double-struck and clashed. **Removed the sampled kick/snare/hat/ohat**; the break
  is now the only drum source, with sub + synth voices + dust + fills over it.
  Side-chain re-keyed to `brk` (sub ducks to the break). -> **`techno_v7.wav`**,
  -13.0 LUFS / -1.1 dBTP.
- **Minimal pass** (user: "more minimalistic, the fill/riser is bad, different key
  for the sub, remove the bells"). Palette cut to **four elements - `brk`, `sub`,
  `ep`, `vinyl`**; removed the sampled kit rows, `strings`, `bell`, `horn`, `stab`,
  `roll`, `rise`. **Sub re-keyed**: it was playing D-G-Bb-A while the chord loop is
  **Am-Bb-Dm-A7**, so it clashed on two chords; now follows the real roots
  **A-Bb-D-A** (`notes=55|58.27|73.42|55`). One-bar stop kept.
  -> **`techno_v8.wav`**, 228.6 s, -13.0 LUFS / -1.1 dBTP; stop verified
  (36-39 -12.6 dB, 39-40 -29.8 dB, 40-43 -12.2 dB). Stems: sub RMS -12.2,
  brk -23.8, ep -22.8, vinyl -32.4. Note: this still uses the **Amen sample** for
  `brk`; awaiting the user's choice of sample vs constructed break.
- **Sub improved** (user: "only the sub needs to be improved"). New
  `templates/sub_min.txt` (this song only; `sub.txt` untouched for `triphop`):
  root sine + 2nd (0.32) + 3rd (0.12) harmonics for definition, a small onset pitch
  drop (1.5 Hz) for punch, an attack/sustain/decay/**release** envelope over the
  2-bar note, and **no `asubboost` / low-shelf bump** (that was the woolly boom).
  Level trimmed. Sub stem peak -4.1 -> -9.9 dB, RMS -12.2 -> -15.4 dB.
  -> **`techno_v9.wav`**, -13.0 LUFS / -2.9 dBTP.
- **Break loop fixed** (user: "the break is not evenly looped"). Root cause: the
  Amen file is **not** 136 BPM as named - its pattern repeats every **1.605 s**
  (a 1-bar period at ~149.5 BPM), so `rate=0.617647` (assuming 136) made the 2-bar
  window mismatch the phrase and every repeat jumped. Correct rate = 84/149.53 =
  **0.56176**, trim 2 bars. Verified: brk self-correlation at the **5.7143 s** loop
  point = **0.957** (tiles exactly).
- **Async sub** (user: "its own melody line, asynchronous"). New
  `templates/sub_async.txt`: a 20-note A-minor melody gated on its own **0.69 s**
  clock (not the bar's 0.7143 s) over a **13.8 s** phrase, so it drifts against the
  2.857 s bar; laid back 0.13 s; side-chain ducking removed (`ratio=1`).
- **Sub extent** (user: "as long as the melody line of the synths, nowhere else"):
  sub gain is 0 before bar 16 (it used to enter at 8, alone); it now enters with the
  piano and leaves with it. Verified low-band (<80 Hz) RMS: bars 8-16 **-34.6 dB**
  (same as intro) vs bars 16-24 **-15.0 dB**.
  -> **`techno_v12.wav`**, -13.0 LUFS / -2.4 dBTP.
- **Bass note length = synth note length** (user: "the bass notes should be as long as
  the synth lines too"). The sub's `unit` is now `{{bar}}`, so every note holds one
  bar (the `ep` holds one chord per bar); the melody is a **5-bar** phrase (5 notes)
  so it still drifts against the 8-bar harmony, laid back 0.13 s, with attack/
  sustain/release. Verified: sub amplitude-envelope period **2.850 s** vs bar
  **2.857 s** (corr 0.942).
  -> **`techno_v13.wav`**, -13.0 LUFS / -3.7 dBTP.
- **Sub quiet + punchy** (user: "reduce its volume a lot, make it punchy"). `amp`
  0.55 -> 0.26, boost 1.1 -> 0.9; envelope now fast attack (`atk=60`, ~16 ms), low
  sustain (0.35), a short pitch thump (`drop=0.25`, `rate=70`) and harmonics that
  decay in ~60 ms (`pdec=16`) over the sustained sub. Sub RMS -12.1 -> **-20.7 dB**
  (-8.6 dB), crest 4.6 -> **9.0 dB** (punchier). Note length still one bar.
  -> **`techno_v14.wav`**, -13.0 LUFS / -1.1 dBTP.
- **Cover + YouTube video** (user request). Cropped `image.jpg` (1152x1712) to a
  1080x1080 square that keeps the "ASYNCHRONOUS" title and drops the Grok
  watermark -> `output/triphop_samples/cover.jpg`. Built
  `output/triphop_samples/ASYNCHRONOUS_1080p.mp4`: 1920x1080 H.264 High / AAC 320k
  48 kHz stereo, 228.57 s, `+faststart`, 1 s fade-in / 2 s fade-out, the cover
  centred on a blurred+darkened copy of itself. ~19 MB.
- **Vinyl darker + quieter** (user: "vinyl noise too high ... low pass ... mellow like
  brown noise"). New `templates/vinyl_brown.txt`: 1-pole low-pass at 500 Hz (a true
  -6 dB/oct "brown" tilt), a 2.2 kHz 2-pole roll-off and a 180 Hz low shelf; amp
  0.22 -> 0.26 but the low-pass removes the hiss, so the bed is darker and ~9.5 dB
  quieter (RMS -32.4 -> **-42.9 dB**; >8 kHz -39 -> **-83.7 dB**). Master
  `techno_v16.wav`.
- **Video re-rendered**; the earlier cut is kept as `ASYNCHRONOUS_1080p_v1.mp4`, the
  new one is `ASYNCHRONOUS_1080p.mp4` (from `techno_v16.wav`, 18.9 MB).
- **Intro shortened by two bars** (user: "trim the first two bars of the video").
  `techno_v17.wav` is `techno_v16.wav` cut at 5.714286 s (verified: the trimmed first
  second matches the old master at sample 274286 / 5.714292 s, MSE 0.0) -> 222.857 s.
  The video was re-rendered from it (18.3 MB); the untrimmed brown-vinyl cut is kept
  as `ASYNCHRONOUS_1080p_v2.mp4`.
- **Vinyl -> a real record groove from YouTube** (user: "download from youtube, this
  is bad too"). `samples.py` now fetches **YouTube rows** with `yt-dlp`
  (`--download-sections`, 90 s from the URL's `t=`); the manifest records the source
  URL and notes it is not CC-licensed (noncommercial use). The sample is "Old Vinyl
  Record Crackle On Loop for 1 Hour" at `t=120`; the vinyl stem is a sampler row
  (`pat=0, pat_bars=31, trim=88.571429`) **as-is** - user: "use the vinyl sample as
  is", so no `fx`; then a slight **-1.9 dB gain trim** (`gain=0.8`) -> RMS
  **-36.4 dB**. (Only the sampler's mono fold otherwise.) Rejected on the way: the
  modelled/brown beds, Freesound 464396, and the "real silent groove" video
  (RMS -42, 49 dB crest - too sparse). Masters `techno_v28.wav` / trimmed
  `techno_v29.wav`; video re-rendered (18.3 MB), previous kept as
  `ASYNCHRONOUS_1080p_v8.mp4`.
- **Cover art:** vertical **XYZZY** in **Times New Roman** (system `times.ttf`,
  render-only) with a multi-colour glitch - cyan/red/magenta/green/yellow ghosts, a
  white core, grain - centred on the cover. `cover_v1.jpg` keeps the clean art; the
  video was re-rendered from the new cover (`ASYNCHRONOUS_1080p.mp4`, 13.0 MB), the
  previous cut kept as `ASYNCHRONOUS_1080p_v9.mp4`.

### Optional next (samplers)

- Keep the Amen break stereo (the sampler folds everything to mono today).
- A `Sends` table so a sampler stem can hit the project reverb/delay.
- Re-encode the `## Samplers` graph so a *missing* sample file fails with the exact
  row, not a filter error (e.g. `rim`/`snare-short` are fetched but unused).
- `fftechno/md.py` is now black-clean; the old note about it is resolved.

## Done - `psych` (1960s psychedelic rock / wall of sound)

110 BPM, 110 bars = 4:00, E minor, instrumental, **no samples**. Built after the
request "psychedelic 1960s rock or stoner rock with wall of sound, without samples,
heavy reverb"; the psych direction was taken.

- **New templates** (all `aevalsrc`): `guitar_fuzz.txt` (root/fifth/octave power-chord
  wall, detuned pairs, tanh fuzz, cab EQ, phaser, slap), `guitar_lead.txt` (fuzz lead
  with vibrato + EQ), `organ.txt` (square drawbars, tremolo + chorus), `bass_rock.txt`
  and `tamb.txt`. Drums reuse `kick_trip/snare/tom/hat_step/ride/crash`; the wash
  reuses `pad.txt`.
- **Wall of sound**: 13 stems - two detuned fuzz guitars panned 0.85/0.15 and
  0.15/0.85, organ chord, mellotron pad, tambourine, rock kit; `stereo_width` 1.25,
  bus compressor for glue.
- **Heavy reverb**: new optional `reverb_seconds` scalar in `song.md` (default 2.2,
  verified byte-identical for existing songs) builds a **5.5 s** IR in `make_ir`;
  `reverb_send` 0.55, `reverb_wet` 1.0. Measured tail: -22.6 / -29.3 / -37.8 dB at
  236/238/239 s.
- **Build**: 96 kHz source (`sr: 96000`) instead of 192 kHz - 192 kHz took >15 min
  and was killed; 96 kHz is still >4x the 9 kHz guitar low-pass.
- **Master**: 240.000 s, -12.9 LUFS, -0.9 dBTP, LRA 2.9 LU.
- **Bug found and fixed**: `guitar_lead` (vibrato + aphaser + aecho + EQ) grew
  unstable over the full 240 s (peak `inf` / RMS `nan`); removing any one of those
  four was stable. The lead now has no phaser/echo (the global reverb covers the
  space) and is stable at peak -3.2 dB across the whole song.
- **Regression**: `synth --song minimal` produces no diff; the default IR hash is
  identical.

### Optional next (psych)

- Per-stem reverb sends (the `Sends` table, still in "Optional next" above) so the
  kick/bass stay dry while the guitars wash.
- A vocal (spoken/TTS) or a synth "vocal" lead if the instrumental needs a hook.

## Done - `stoner` (stoner rock)

76 BPM, 76 bars = 4:00, D minor / drop-D, instrumental, no samples. Built after
"psych is not that nice; do stoner rock".

- **New template**: `guitar_wah.txt` (single-note fuzz + phaser; no vibrato/echo,
  stable over 240 s). Reuses `guitar_fuzz.txt`, `bass_rock.txt`, `organ.txt` and the
  drum templates.
- **Riff**: driving 8th-note D-D-F-G / D-D-F-A, two detuned guitars panned 0.8/0.2
  and 0.2/0.8, thick fuzz bass, big sparse drums, low organ drone in the
  intro/breakdown.
- **Found and fixed the quiet-guitar bug**: `aecho`'s `in_gain x out_gain` was
  attenuating the guitar by ~11 dB (0.7 x 0.4). The stoner guitars use 1.0/1.0 with
  decay 0.1; the guitar then matched the bass in the 300-3k band (both ~-20 dB). The
  80 Hz high-pass was also cutting the D2 fundamental (73 Hz); lowered to 55 Hz.
- **Master**: 240.000 s, -12.9 LUFS, -1.1 dBTP, LRA 2.9 LU. 5.0 s IR.
- **Stems**: 11, all peaks < 0; the two guitars differ.

## Done - `stoner_samples` (sample-based stoner rock)

80 BPM, 80 bars = 4:00, C minor / drop-C, built from downloads.

- **Sources** (`samples/manifest.md`, set `stoner_kit`): Pearl Master Studio acoustic
  drums (CC-BY 3.0), FreePats `FSBS-dist1` pre-distorted electric guitar and
  `electric-bass-YR` picked bass (both CC0). The FLAC sources are downloaded under
  `.wav` names and `prepare` transcodes them to 48 kHz PCM.
- **Sampler extension** (`fftechno/sampler.py`): `notes`/`root` per-hit pitch
  (`asetrate`), a per-hit `fx` chain (`;`-separated), a **multi-sample map**
  (`path@root|...`, nearest root per note: C2/F2/C3 guitars, C3/G3 lead, C/E2 bass),
  and `pat` instruments now build one bar and loop it with `asetpts` + `atrim` +
  `apad=whole_len` + `aloop` (sample-accurate; the graph is ~4 KB instead of 640
  chains). Fixed a `pat` semantics bug: the list is **step indices**, not a gate
  pattern - the riff now plays 8ths at 0/2/4/6/8/10/12/14, not 16 duplicated hits.
  `hits` still uses the per-hit + silent-bed path.
- **Song**: drop-C riff C-C-Eb-F / C-C-Eb-G on two detuned sampled guitars, sampled
  bass and Pearl drums; 10 stems; 5 s room.
- **Master**: 240.000 s, -13.0 LUFS, -2.0 dBTP, LRA 9.1 LU. Build ~14 s.
- **Regression**: `synth --song triphop_samples` still renders; the `pat` loop change
  alters the generated triphop_samples graphs (expected) but not the audio design.
- **Take 2 (tone fix)**: the pre-distorted FreePats guitar was too dark (growl ~14 dB
  down). Switched to the clean DI (`FSBS-direct`) + an Orange-style fuzz chain, power
  chords (`chord=1|1.5:0.7|2:0.45`), sustain (trim 1.2 s) and a 2-bar riff
  (`pat_bars=2`). Added `chord` and `pat_bars` to the sampler. Growl now ~4 dB below
  the low-mids. Master `techno_v3.wav`: -13.0 LUFS / -2.7 dBTP, LRA 6.6, build ~13 s.
- **Drums pass**: added `rr` (round-robin) and `jitter` (humanize) to the sampler.
  The kit now uses round-robin snare/tom (3 Pearl samples each), ghost notes +
  velocity accents, a groovier kick (1 / 2& / 3 / 4&) and tone shaping (kick
  weight + click, snare body + crack, compression). Master `techno_v4.wav`:
  -13.0 LUFS / -2.6 dBTP, LRA 6.7.

### Optional next (sampler)

- A dedicated drum room/plate reverb send (today the drums share the global 5 s room).
- A sampled organ or tambourine for the chorus.
- Longer-form arrangement variation (a real bridge, not just section gains).
