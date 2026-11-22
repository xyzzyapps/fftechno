# ffmpeg as a synthesizer: an `aevalsrc` / `aeval` cookbook

This is a from-scratch tutorial on building musical instruments and whole tracks out
of ffmpeg's expression filters, `aevalsrc` and `aeval`. It starts with the smallest
possible primitives and builds up to drums, basses, leads, pads, a saxophone, a Rhodes
piano, vinyl noise, step sequencing, swing, randomness and effects - all the machinery
this project (`fftechno`) uses. Every claim here was checked against the local build:

```
ffmpeg version 9.0.2-full_build-www.gyan.dev
```

Two things up front, because they surprise most people coming from a DAW:

1. **There is no oscillator object.** There is only a *formula evaluated once per
   output sample*. An "oscillator" is a formula in the variable `t` (time). A "synth"
   is a formula plus a chain of ordinary ffmpeg audio filters.
2. **There is no MIDI and nothing is realtime.** The whole thing is a batch renderer:
   you describe a sound as maths over time, ffmpeg bakes it to samples, and you listen
   to the file. This has real consequences, and they are spelled out in section 9.

Everything below is executable: paste any `ffmpeg ...` line into a shell and play it
with `ffplay` instead of `-f null -`.

---

## 1. The two filters

### 1.1 `aevalsrc` - a source (generator)

`aevalsrc` has **no input**. It manufactures audio from one expression per channel.
Its options (from `ffmpeg -h filter=aevalsrc`):

| option | short | meaning | default |
|--------|-------|---------|---------|
| `exprs` | - | `|`-separated list of per-channel expressions | `sin(2*PI*440*t)` |
| `sample_rate` | `s` | sample rate | `44100` |
| `duration` | `d` | duration (seconds, or `1.5s`, `200ms`, ...) | none |
| `channel_layout` | `c` | e.g. `mono`, `stereo` | (from expr count) |
| `nb_samples` | `n` | samples per requested frame (buffer size) | `1024` |

Variables available **inside** the expression:

| variable | meaning |
|----------|---------|
| `t` | time in seconds (a float, increments by `1/sample_rate` each sample) |
| `n` | the sample index, starting at 0 |

Constants: `PI`, `E`, `PHI` (check with the notes in section 2). Note there is **no
`sr` variable** - if you need the rate inside the expression you pass it in literally.

```bash
# A440 for one second, mono, 48 kHz  ->  play with ffplay instead of -f null -
ffmpeg -f lavfi -i "aevalsrc='sin(2*PI*440*t)':s=48000:d=1" -f null -

# stereo: two expressions separated by |
ffmpeg -f lavfi -i "aevalsrc='sin(2*PI*440*t)|sin(2*PI*220*t)':s=48000:d=1" -f null -
```

### 1.2 `aeval` - an effect (per-sample transform)

`aeval` has **one audio input** and rewrites each sample with an expression. Use it to
modulate, attenuate, distort or combine existing audio mathematically. Variables:

| variable | meaning |
|----------|---------|
| `val(ch)` | the current input sample of channel `ch` (0-based) |

`n` and `t` are also available. Note the input accessor is **`val(0)`** on this build;
`s(0)` is *not* accepted (verified - `Invalid chars`).

```bash
# take a sine and halve it with aevalsrc's own maths
ffmpeg -f lavfi -i "sine=frequency=440:duration=1" -af "aeval='0.5*val(0)'" -f null -
```

### 1.3 How this project uses them

A "song" is a folder of markdown. `sounds.md` names an instrument and a template;
the template is a text file of `aevalsrc ... [src];[src]<filters>...[out]`.
`fftechno/synth.py` substitutes `{{key}}` values and expands `{{if_steps(...)}}`
into a nested `if(...)` ladder, writing a finished filtergraph to
`filters/<song>/<name>.txt`. `fftechno/audio.py` then renders **each instrument alone**
to a WAV (`output/<song>/stems/<name>.wav`) - exactly a DAW "freeze/bounce to stem" -
and `fftechno/arrangement.py` mixes the stems with automation, side-chain and reverb.

So when this document says "instrument", it means one `aevalsrc` graph rendered to one
stem. The rest of the track is a normal ffmpeg mix.

---

## 2. Primitives

The expression evaluator is documented in the libavutil "Expression Evaluation"
section. What is available (verified against ffmpeg 9.0.2):

- **Operators:** `+ - * / ^`, unary `+`/`-`, and `;` to evaluate two expressions in
  sequence (`expr1;expr2` returns `expr2`).
- **Functions:** `abs, acos, asin, atan, atan2, between, bitand, bitor, ceil, clip,
  cos, cosh, eq, exp, floor, gauss, gcd, gt, gte, hypot, if, ifnot, isinf, isnan, ld,
  lerp, log, lt, lte, max, min, mod, not, pow, print, random, randomi, root, round,
  sgn, sin, sinh, sqrt, squish, st, tan, tanh, taylor, time, trunc, while`.
- **Constants:** `PI`, `E`, `PHI`.
- **Scratch variables:** ten slots via `st(idx, expr)` and `ld(idx)`, `idx` = 0..9.
- **Number suffixes:** SI prefixes (`k`, `M`, `G`, ...) - e.g. `2k` is 2000.

Practical notes:

- There is **no `%`**; use `mod(x, y)`. There is **no `=` assignment**; use `st`/`ld`.
- `if(cond, a, b)` is the conditional; `if(cond, a)` gives `a` or `0`.
- Boolean-ish values are numbers: `gt`, `lt`, `eq`, `between` return `0`/`1`, so they
  are used as **gates** (multiply by them to switch a signal on/off).
- Truthiness: non-zero is true; `*` behaves like AND, `+` like OR.
- The evaluator is **per sample**. Any expression is evaluated ~`sample_rate * seconds`
  times; `random()` therefore produces a new value every sample (section 6).

### 2.1 `st`/`ld` - the "variables" you were told do not exist

Older project notes claim ffmpeg eval "has no user variables". That is not quite true:
there are **ten** scratch slots (0..9), shared *per expression*:

```bash
# store 440 in slot 0, then use it twice (verified)
ffmpeg -f lavfi -i "aevalsrc='st(0,440); 0.5*sin(2*PI*ld(0)*t)' :s=48000:d=1" -f null -
```

The catch: `random(idx)` uses the **same ten slots** to hold its PRNG state, and the
project's templates are generated by literal text substitution, so repeating a
constant inline is simpler than threading `ld` through a hand-written template. That is
why the generated graphs are full of repeated numbers.

---

## 3. The oscillator library

There is no oscillator primitive - you write one. These are the building blocks, all
in terms of a frequency `f` and `t`:

| wave | expression | notes |
|------|------------|-------|
| sine | `sin(2*PI*f*t)` | pure tone |
| saw (rising) | `mod(f*t,1)*2-1` | all harmonics; buzzy |
| square | `gt(mod(f*t,1),0.5)*2-1` | odd harmonics only |
| pulse (width `p`) | `gt(mod(f*t,1),p)*2-1` | `p=0.5` is a square; moving `p` = PWM |
| triangle | `1-4*abs(mod(f*t,1)-0.5)` | softer than square |
| white noise | `random(0)*2-1` | new value per sample |

**Phase is the key idea.** `mod(f*t,1)` is a phase ramp `0 -> 1` that repeats `f`
times per second. Reset it (`mod(t,step)` inside the argument) and the wave restarts
at a grid boundary; leave it (`f*t`) and it free-runs. That single choice is the
difference between a *plucked* sound and a *drone* (section 4.3).

### 3.1 Envelopes

An envelope is just a function of time multiplying the oscillator.

| envelope | expression |
|----------|------------|
| decay (percussive) | `exp(-k*t)` - `k` larger = shorter |
| attack + decay (AD) | `(1-exp(-a*t))*exp(-d*t)` |
| retriggering decay | `exp(-d*mod(t,period))` - restarts every `period` seconds |
| sustain + release | `(sus+(1-sus)*exp(-d*t))*(1-exp(-r*(T-t)))` - `T` = note length |
| gate (on/off) | `gt(...)`, `lt(...)`, or a step lookup (section 4) |

`mod(t, period)` is the sequencer's clock: the envelope resets on every tick and a
*gate* decides whether that tick makes a sound. This is why a "mother" template like
`kick.txt` (retriggers every beat, always on) and a gated variant like
`kick_trip.txt` (retriggers every 16th, gate-selected) are only one factor apart.

### 3.2 Modulation

| effect | expression |
|--------|------------|
| vibrato | `sin(2*PI*f*t + depth*sin(2*PI*vf*t))` |
| FM (2-op) | `sin(2*PI*fc*t + I*sin(2*PI*fm*t))` |
| tremolo / AM | `(1+a*sin(2*PI*amf*t))*sin(2*PI*f*t)` |
| detune / supersaw | `saw(f*t) + det*saw(f*d*tune*t)` |
| PWM | pulse whose width `p` comes from a slow LFO (see `lead_pwm.txt`) |

---

## 4. Building an instrument

Every instrument in this project is the same four-part recipe:

```
out = amp * gate * envelope * excitation   ->   filter chain
```

- **excitation** - oscillator(s) and/or noise,
- **envelope** - attack/decay, with a retrigger period,
- **gate** - a step lookup selecting *which* ticks fire (0/1),
- **filter chain** - tone shaping, saturation, EQ (section 7).

### 4.1 Worked example - the kick

`templates/kick.txt` is a pitch-swept sine plus three layers:

```
amp * (
    sin(2*PI*( f0*mod(t,beat) + (sweep/rate)*(1-exp(-rate*mod(t,beat))) ))
        * exp(-decay*mod(t,beat))          # body: pitch falls f0+sweep -> f0
  + click_amt   * sin(2*PI*click_f  *mod(t,beat)) * exp(-click_decay*mod(t,beat))  # click
  + sub_amt     * sin(2*PI*sub_f    *mod(t,beat)) * exp(-sub_decay  *mod(t,beat))  # sub
  + noise_amt   * (random(0)*2-1)                 * exp(-noise_decay*mod(t,beat))  # beater
)
[src]equalizer=f=..:t=q:w=1:g=..,asoftclip=type=tanh:threshold=..,lowpass=..,aresample=48000[out]
```

The `(1-exp(-rate*...))` term is the classic **pitch envelope**: at the hit the
frequency is `f0 + sweep`, and it decays to `f0`. `mod(t,beat)` retriggers on the
beat. A `lowpass` and a tanh `asoftclip` round it off.

### 4.2 The instrument catalogue

How each project instrument is assembled (a `|` here is the template's
`{{ if_steps(notes; grid; default) }}` step lookup):

| instrument | template | excitation | envelope | notable filters |
|------------|----------|-----------|----------|-----------------|
| kick | `kick.txt` | swept sine + click sine + sub sine + noise | `exp(-d*mod(t,beat))` | `equalizer`, `asoftclip`, `lowpass` |
| gated kick | `kick_trip.txt` | same | `exp(-d*mod(t,step))` + gate | same |
| snare | `snare.txt` | tone sines + noise | `exp(-d*mod(t,step))` | `highpass`, `lowpass` |
| hat | `hat.txt` / `hat_step.txt` | noise | `exp(-d*mod(t,step))` + gate + `vel` | `highpass` |
| open hat | `ohat_dyn.txt` | noise | decay *and* velocity modulated per step | `highpass` |
| shaker / rim | `shaker.txt` / `rim.txt` | noise (+ a tone for the rim) | `exp(-d*mod(t,step))` | `highpass` |
| bass | `bass.txt` / `bass_gate.txt` | saw + sub sine + detuned saw, **phase reset per step** | `exp(-d*mod(t,step))` + gate | `lowpass` (resonant), `equalizer`, `asubboost`, `asoftclip` |
| reese (dub bass) | `reese.txt` | square + detuned square + sub, **free phase** | `exp(-d*mod(t,beat))` | two `lowpass` (24 dB) + resonant `equalizer` |
| acid (303) | `acid.txt` | saw with per-step pitch **bends**, vibrato | `exp(-d*mod(t,step))` + accents | HP, split bright/dark LP crossfade, resonant peaks, `acrusher` |
| lead (FM) | `lead_fm.txt` | `sin(fc*t + I*sin(fc*ratio*t))` | `exp(-d*mod(t,step))` + gate | `highpass`, `aphaser`, `asoftclip` |
| lead (PWM) | `lead_pwm.txt` | three pulse oscillators, LFO width | `exp(-d*mod(t,step))` + gate | `highpass`, `asoftclip` |
| pad / stab | `pad.txt` / `stab.txt` | three summed note ladders = a **chord** | `pad`: slow swell; `stab`: `exp(-d*..)` | `highpass`, `lowpass` |
| conga / tom | `conga.txt` / `tom.txt` | swept sine per step | `exp(-d*mod(t,step))` | `highpass`, `aecho` |
| blow (candle puff) | `blow.txt` | noise | `(1-exp(-a*u))*exp(-d*u)`, `u=mod(max(0,t-at),period)` | resonant `equalizer`, `asoftclip`, **ping-pong `aecho`** |
| Sax (this project, `sax.txt`) | see 4.4 | saw + detuned saw + breath noise + vibrato | ADSR over a quarter-note grid | two formant `equalizer` peaks, `asoftclip`, `lowpass` |
| Rhodes (this project, `rhodes.txt`) | see 4.5 | three **FM** voices = a chord | ADSR over a half-note grid | `highpass`, `equalizer`, `asoftclip` |
| vinyl (this project, `vinyl.txt`) | see 4.6 | hiss + sparse random pops | none (a bed) | band-pass `highpass`+`lowpass`+`equalizer`, slow AM "wow" |

### 4.3 Free phase vs reset phase (the "click" decision)

```
# free-running (drone): phase never resets -> smooth, no click
mod(f*t,1)*2-1

# reset at each step: the oscillator restarts from the same point each tick
mod(f*mod(t,step),1)*2-1
```

`bass.txt` uses the reset form on purpose (`mod(notes*mod(t,step),1)`): every 16th
starts the saw at phase 0, which gives a tight, gated, "pumping" bass - and a tiny
discontinuity that reads as attack. `reese.txt` uses the free form for a continuous,
smeared drone. Choosing per instrument is most of the art here.

### 4.4 The saxophone

The requested horn, in `templates/sax.txt`, is a *reed* saw driven through two
resonant formant peaks, with breath noise at the attack and delayed vibrato. Its
expression (read the four-part shape):

```
amp
* gate                              # if_steps(gates; qgrid; 0)
* (1-exp(-atk*mod(t,qstep)))        # attack
* (sus+(1-sus)*exp(-dec*mod(t,qstep)))          # decay to a sustain
* (1-exp(-rel*(qstep-mod(t,qstep))))            # release at the note's end
* ( (mod(notes*t + vib_amt*sin(2*PI*vib_f*t),1)*2-1)     # reed saw + vibrato (phase mod)
  + det*(mod(notes*detune*t,1)*2-1)                      # detuned second reed
  + breath*(random(0)*2-1)*exp(-breath_dec*mod(t,qstep)) )  # air
[src]highpass=f=120,
     equalizer=f=900:t=q:w=1.1:g=8,        # lower formant ("body")
     equalizer=f=2100:t=q:w=1.0:g=5,       # upper formant ("bite")
     asoftclip=type=tanh:threshold=0.6,    # reed rasp / harmonic enrichment
     lowpass=f=7200, lowpass=f=19000,
     aresample=48000[out]
```

The note frequency is a step lookup (`notes`), the note length is the *grid period*
`qstep` (a quarter note), and `vib_amt*sin(...)` added inside the `mod()` is a phase
modulation, i.e. **vibrato**. The two `equalizer` peaks are the horn's formants; moving
them (and the `det`/`breath` mix) moves you from "kazzoo" to "sax".

### 4.5 The Rhodes (FM chord)

A Rhodes is the classic 2-operator FM bell. Each voice is

```
sin(2*PI*f*t + I*exp(-mdec*K)*sin(2*PI*f*ratio*t))     # K = mod(t,hstep)
```

- the modulator (`sin` at `f*ratio`) adds a bright "tine" attack whose index
  `I*exp(-mdec*K)` decays quickly, leaving a mellow body;
- `ratio=2` gives the bell octave;
- three such voices (`n1`,`n2`,`n3`) **summed** make a chord, because one `aevalsrc`
  is monophonic and polyphony is achieved by adding oscillators.

`rhodes.txt` runs them on a half-note grid (`hgrid`/`hstep`), so the chord changes
every 1.36 s over a 4-bar cycle - a comping progression encoded entirely in note
lists.

### 4.6 Vinyl dust

`vinyl.txt` is a bed, not a note - an envelope-free sum:

```
amp * ( hiss*(random(0)*2-1)                              # surface hiss
      + pop*(random(1)*2-1)*gt(random(2), 0.9999985) )    # sparse clicks
    * (wow + wow_amt*(0.5+0.5*sin(2*PI*wow_f*t)))         # slow "wow" AM
[src]highpass=f=1400,lowpass=f=9000,equalizer=f=3000:t=q:w=1:g=4,lowpass=f=19000
```

`random(1)` is the click *sample*, `random(2)` is a per-sample die: when it exceeds
`0.9999985` (about 1 sample in 700k, so a handful per minute) a click fires. The
`equalizer`+`highpass` band-limit it to a crackly 1.4-9 kHz.

---

## 5. Sequencing

### 5.1 The grid is just an integer function of time

```
bar  = 60/bpm*4                 # seconds per bar (4 beats)
step = bar/16                   # a 16th
grid = floor(mod(t, bar)/step)  # 0,1,2,...,15,0,1,... one pass per bar
```

`floor(mod(t,bar)/step)` counts 16th notes and loops each bar. Change the divisor
(`beat = bar/4`, or a full phrase) and you change the resolution. Change the modulus
(`bar` -> `bar*4`) and the pattern spans 4 bars instead of one.

### 5.2 `{{ if_steps(...) }}` -> a nested `if` ladder

This project stores patterns as `|`-separated lists in markdown and expands them:
`{{if_steps(notes; grid; note_def)}}` becomes

```
if(eq(grid,0),notes0, if(eq(grid,1),notes1, ... , note_def))))
```

- **gate** - a list of `1`/`0`; multiply the signal by it.
- **notes** - a list of frequencies; used as the oscillator's `f`.
- **vel / accents** - a list of velocities, indexed the same way.
- **bends** - a list of pitch offsets (the 303 slide).

A tiny hand-written example - a 4-step melody at 120 BPM:

```bash
# bar=2s, step=0.5s; notes 220,330,440,330 on steps 0..3
ffmpeg -f lavfi -i "aevalsrc='0.5*exp(-8*mod(t,0.5))*sin(2*PI*if(eq(floor(mod(t,2)/0.5),0),220,if(eq(floor(mod(t,2)/0.5),1),330,if(eq(floor(mod(t,2)/0.5),2),440,330)))*t)':s=48000:d=4" -f null -
```

### 5.3 Note length, not just note pitch

The envelope's retrigger period chooses the note length:

| want | use |
|------|-----|
| 16th plucks | `mod(t,step)` |
| 8th notes | `mod(t, 2*step)` |
| quarter-note lead | a grid whose period is a quarter (`qgrid`/`qstep`) |
| a held drone | no `mod` at all - free phase |

This is the subtle bit: **the sequencer resolution and the note length are the same
number.** To get long notes on a fine grid you must either use a coarse grid (fewer,
longer steps) or craft a multi-segment envelope.

### 5.4 Multi-bar phrases and chords

- **Phrases:** make the grid period name-length, e.g.
  `floor(mod(t, 4*bar)/(bar/4))` gives 16 quarter-note slots across 4 bars - the sax
  `notes` list is exactly that (16 entries).
- **Chords / polyphony:** one `aevalsrc` is monophonic. Sum several note ladders
  (`n1`,`n2`,`n3` in `pad.txt`/`stab.txt`/`rhodes.txt`) or several voices to get
  harmony. Cost is linear in voices.
- **Arrangement** is *not* in the instrument: it lives in `song.md`'s `Sections`
  table, where a cell is the stem's gain over a bar range. `fftechno` turns each row
  into a nested `if(lt(t,...))` gain expression and applies it with
  `volume=volume='...':eval=frame`. That is bar-level automation - a DAW arrangement
  lane, sampled once per audio frame.

---

## 6. Randomness

### 6.1 `random(idx)` - a deterministic PRNG

`random(idx)` returns a pseudo-random value in `[0,1)` using one of the ten scratch
slots (`idx` 0..9) as its state. It is **stateful**: each evaluation advances the
state, and since the expression runs once per sample, you get a fresh number each
sample. Two properties matter:

- **It is reproducible.** Two renders of the same graph are byte-identical
  (verified: `random(0)*2-1` produced the same MD5 on repeated runs). Different
  `idx` values are independent streams.
- **The seed is a slot.** You can pin it: `st(0, 42); random(0) ...`.
  The project relies on the un-seeded default being stable for a fixed ffmpeg build;
  a different build may reorder the stream.

Uses: white noise (`random(0)*2-1`), dust/click dies (`gt(random(2), th)`), and
"humanising" (below).

### 6.2 Per-step randomness without an RNG

`random(idx)` varies **per sample**, so you cannot use it directly for a *per-step*
value (velocity, ring length) - it would jitter within the step. The project's trick
is to **hash the step index** with a fast oscillating irrational:

```
0.5 + 0.5*sin(floor(t/step) * gold)     # gold = 2.399963 (a golden-ratio phase)
```

Because `floor(t/step)` is constant across a step, this value is constant per step but
wanders between steps - deterministic quasi-noise that never settles into a fixed
1-bar loop. `ohat_dyn.txt` scales each hit's *decay* and *velocity* with two such
sequences (`gold`, `gold2`); `hat_step.txt`/`shaker.txt` use it for accent.

### 6.3 Noise vs. musical randomness

- **Noise** (hiss, snare body, breath): `random(0)*2-1`, then band-limit it with
  `highpass`/`lowpass`/`equalizer` so it reads as a texture, not a hiss.
- **Humanising** (velocity, timing, decay): a quantised hash (§6.2) or `randomi`.
- **Timing jitter** is the hard one: there is no "nudge step 7 by 12 ms" primitive;
  you would warp the grid (section 7 on swing is the same tool).

---

## 7. Swing (and other time warps)

**Straight** 16ths are `floor(mod(t,bar)/step)`. To **swing**, delay every second 16th
without moving the first: the classic "shuffle" is a pairwise time warp. Work in
*pairs* of 16ths:

```
pair  = 2*step                                        # the width of two 16ths
k     = floor(mod(t,bar)/pair)                        # which pair (0,1,2,...)
u     = mod(mod(t,bar), pair)/pair                    # position inside the pair, 0..1
s     = 0.585                                         # swing: 0.5 = straight; 2/3 = triplet
swing_grid = 2*k + gt(u, s)
```

Read it: the first 16th of the pair lasts `s` of the pair, the second lasts `1-s`.
With `s=0.5` you get straight 16ths; with `s=0.585` a gentle 58% shuffle; with
`s=2/3` a full triplet feel. The result is still an integer step index, so every
`gate`/`notes` list and `if_steps` lookup works unchanged. Swap `grid` for
`swing_grid` in `song.md`/`sounds.md` and the whole kit swings together.

The same idea covers other warps:

| warp | how |
|------|-----|
| swing / shuffle | pairwise warp above |
| triplet grid | use `bar/12` as the step and a triplet note list |
| half-time feel | use `bar/8` (8ths) with a sparse kick - the project's trip-hop kick |
| humppa / dotted | warp `s` per pair (e.g. alternate 0.585 and 0.667 per bar) |

Because it is a pure function of `t`, the swing is deterministic and identical on
every render - no "groove template" file required.

---

## 8. Effects

`aevalsrc` only makes a raw signal. Everything a DAW would call an *effect* is a
**separate ffmpeg audio filter** appended to the graph (per instrument) or to the mix
bus (`fftechno/arrangement.py`) or the master (`fftechno/audio.py`). Mapping to the
DAW/Electribe world:

| ffmpeg filter | DAW / workstation equivalent | project use |
|---------------|------------------------------|-------------|
| `lowpass`, `highpass` | filter / cutoff | every synth; resonant 24 dB bass |
| `equalizer` (`t=q`, `g`) | parametric EQ (bell/shelf) | formants, kick body, master air |
| `asoftclip=type=tanh` | saturation / overdrive | kick, bass, lead, sax rasp |
| `acrusher` | bitcrusher / decimator | the 303 |
| `asubboost` | sub / bass enhancer | bass |
| `aphaser` | phaser | FM lead |
| `aecho` | delay (multi-tap) | per-instrument delay/reverb send, ping-pong |
| `afir` | **convolution reverb** (loads an impulse response) | the mix reverb (generated IR) |
| `acompressor` | compressor | mix bus glue |
| `sidechaincompress` | **side-chain / ducking** | bass ducks under the kick |
| `alimiter` | brickwall limiter | master ceiling |
| `loudnorm` | LUFS loudness meter + normaliser | 2-pass -13 LUFS master |
| `extrastereo` | stereo width | mix bus |
| `haas` | Haas widener | conga pan |
| `pan` | pan / balance | every stem |
| `volume=...:eval=frame` | fader / automation lane | section gains, fades |
| `asplit` + `amix` | bus routing / group tracks | stems -> sum -> reverb send |
| `adelay`, `apad` | track offset / tail | placement, tails |
| `aresample` (with dither) | sample-rate conversion + dither | 192 k -> 48 k, 16-bit out |

Two project idioms worth copying:

- **A "send" needs a low `in_gain`.** `aecho` cannot null its dry path, so a reverb
  or delay *send* mixes the taps back at a low `in_gain` and lets the wet branch carry
  only the tail (`kick_verb.txt`, `hat_rand.txt`).
- **A delay line is a multi-tap `aecho`, not a loop.** Feedback is faked with repeated
  taps, e.g. `aecho=0.05:1.0:400|1200|2000:0.4|0.18|0.08` for a ping-pong-ish echo
  (`blow.txt`).

Reverb is per-project: `make_ir()` generates `logs/ir.wav` (decaying noise) and the
mix bus runs `afir` against it - a convolution reverb whose "plugin preset" is a
generated file.

---

## 9. How this compares to a DAW / a groovebox (Electribe)

The mental model shift:

| concept | DAW / Electribe | this project |
|---------|-----------------|--------------|
| instrument | a plugin/engine with typed params | an `aevalsrc` expression + filter chain |
| oscillator | an object with `freq`, `shape` | a formula in `t` |
| note on/off | an event with pitch/velocity on a timeline | a step in a `gate`/`notes` list, or an envelope retrigger |
| velocity | per-note parameter | a `vel` list (or a hashed per-step value) |
| polyphony | voices | summing oscillators in one expression |
| step sequencer | pads + pattern grid, 1-4 bars | `floor(mod(t,bar)/step)` + `if_steps` lists |
| song mode | arrange patterns over time | `Sections` table (bar ranges -> gains) |
| motion sequencing | recorded knob automation | `volume=...:eval=frame` section gains |
| choke group | mutes one hit when another fires | multiply two gates (`gate_a*(1-gate_b)`) |
| swing | a groove/shuffle parameter | a pairwise grid warp (section 7) |
| effects | insert/send racks | appended filters; mix-bus chain; IR reverb |
| mixer | faders, pans, busses | `song.md` Boosts/Pan/Effects; `amix`/`sidechaincompress` |
| bounce/freeze | render a track to audio | `audio.render_stems` -> one WAV per instrument |
| mastering | limiter + LUFS meter | `alimiter` + 2-pass `loudnorm` |

What you **gain**: total, exact, code-like control; perfect reproducibility; no plugin
or vendor dependency; every parameter is a diffable text value.

What you **lose / cannot do** (relative to a groovebox):

- No realtime editing, no knobs, no live performance, no motion recording.
- No MIDI in or out (section 10).
- No samples, no wavetables, no "load a break" - you re-synthesise.
- Naive, band-unlimited waveforms: a saw/square **aliases**. The project mitigates
  this by generating at 192 kHz and `aresample`-ing to 48 kHz (the decimation filter
  removes the out-of-band alias images; in-band aliasing remains).
- Cost is per-sample maths: long expressions and high sample rates are slow.
- No note objects means no easy per-note retrigger of an arbitrary melody unless you
  encode it as a step list.

---

## 10. MIDI and realtime - the honest answer

You are right: **this supports neither MIDI nor realtime control.**

- **No MIDI.** ffmpeg has no MIDI input or synthesis. There is no note/event stream,
  no clock, no pitch-bend message. The "score" *is* the expression and the markdown
  around it. The nearest thing to MIDI here is generating the *numbers* a MIDI would
  have carried (frequencies, gates, velocities) and baking them straight into the
  formula.
- **Not realtime.** ffmpeg is a batch pipeline: input -> filtergraph -> output. The
  graph is evaluated as fast as the CPU allows; it is not clocked to wall time and
  there is no way to change a parameter mid-render. Changing anything means editing
  markdown and re-running `python -m fftechno audio`.

The useful, honest workarounds:

| want | how close you can get |
|------|-----------------------|
| *monitor* a graph live | `ffplay -f lavfi "aevalsrc='...':s=48000"` - SDL playback, but the graph is fixed |
| *pace* a render like playback | add `-re` to an input so ffmpeg reads at native rate |
| process a **live input** | feed `-f dshow -i audio="<device>"` through `aeval`, which runs per-sample as data arrives (low-latency), then out to a device |
| *tweak* a param | edit `sounds.md`/`song.md`, rebuild (seconds to minutes) |
| a "performance" | none - the track is a rendered artefact |

So the workflow is **compile, not perform**: author the score as data, bake it, listen,
iterate. That is the whole philosophy of this project, and it is why every parameter
is a markdown cell rather than a knob.

---

## 11. Gotchas, performance, reproducibility

- **`;` is sequencing, not a variable.** `st(0,440); expr` stores then evaluates.
- **No `%`.** Use `mod`. No assignment; use `st`/`ld` (10 slots, shared with `random`).
- **`val(ch)` for `aeval`**, not `s(ch)`, on this build.
- **No `sr` variable** in `aevalsrc` - pass the rate as a literal.
- **`random(idx)` is deterministic per build**, not globally - pin it with
  `st(idx, seed)` if cross-build stability matters.
- **Aliasing.** Generate at a multiple of the output rate (the project uses 192 kHz ->
  48 kHz) and low-pass to taste.
- **Cost.** Evaluation is per sample; `sample_rate * duration` evaluations per
  expression. Keep high-rate/long/dense expressions to the voices that need them.
- **Expression size.** A 16-entry `if_steps` ladder repeated three times in one
  template is normal; a 64-entry ladder repeated six times (a 3-voice, 8-bar FM chord)
  gets heavy. Split into more instruments/stems if a build drags.
- **Tails.** A graph with a delay (`aecho`) or reverb can be longer than the track;
  cut stems with `-t <duration>` (this project's `render_stems` does).
- **DC offset.** Reset-phase oscillators and asymmetric waves can leave DC; a
  `highpass` near 20-40 Hz removes it.

---

## 12. Cheat sheet

```text
# time / index
t                      seconds (float)
n                      sample index (0,1,2,...)

# oscillators (f = Hz)
sine      sin(2*PI*f*t)
saw       mod(f*t,1)*2-1
square    gt(mod(f*t,1),0.5)*2-1
pulse     gt(mod(f*t,1),p)*2-1
triangle  1-4*abs(mod(f*t,1)-0.5)
noise     random(0)*2-1

# envelopes
decay     exp(-k*t)
AD        (1-exp(-a*t))*exp(-d*t)
retrigger exp(-d*mod(t,period))
gate      gt(x,y) | lt(x,y) | if_steps lookup

# sequencer
bar       60/bpm*4
step      bar/16
grid      floor(mod(t,bar)/step)
swing     2*floor(mod(t,bar)/(2*step)) + gt(mod(mod(t,bar),2*step)/(2*step), s)

# modulation
vibrato   sin(2*PI*f*t + depth*sin(2*PI*vf*t))
FM        sin(2*PI*fc*t + I*sin(2*PI*fm*t))
detune    saw(f*t) + det*saw(f*tune*t)

# scratch / randomness
st(i,x); ld(i)          i = 0..9
random(i)               deterministic, per sample, state in slot i
randomi(i,min,max)
per-step hash           0.5+0.5*sin(floor(t/step)*gold)
```

---

## 13. See also (in this repo)

- `templates/` - the finished schematics every example above is drawn from.
- `SPEC.md` section 7-10 - the template language, the mix graph and the master.
- `README.md` - the musician's cheat sheet (which markdown cell does what).
- ffmpeg docs: `ffmpeg -h filter=aevalsrc`, `ffmpeg -h filter=aeval`, and the
  "Expression Evaluation" section of the FFmpeg Utilities manual.

---

## 14. Pure Data `expr~` and Csound

Two other "eval" systems sit next to this one, and they are not the same thing.
The per-sample formula is close to Pure Data's `expr~`. Csound's score
`[ ]` math runs once, when the score is read. The *shape* of this project
(a schematic plus a score, baked to audio) is closer to a Csound orchestra and
score than either formula is.

### 14.1 Three different "evals"

| Name | Where it runs | When |
|------|----------------|------|
| ffmpeg `aeval` / `aevalsrc` | one formula, every output sample | render time, for the whole file |
| Pure Data `expr~` | one C-like formula, every audio sample | the audio callback, live |
| Pure Data `expr` | the same family, control rate | when a message arrives |
| Csound score `[ ]` | `+ - * / % ^` inside a score number | once, while the score is loaded |
| Csound orchestra | opcodes at i-rate, k-rate, and a-rate | each note, then each control period, then each sample |

ffmpeg's evaluator is documented as "Expression Evaluation" in the FFmpeg
Utilities manual (section 2 of this file). Pure Data's is the `expr` family
by Shahrokh Yadegari (`expr`, `expr~`, `fexpr~`), originally from IRCAM jMax.
Csound's score feature is the manual page "Evaluation of Expressions": arithmetic
in square brackets, plus macros and `~` for a random value in 0..1.

### 14.2 Pure Data `expr~`

`expr~` evaluates one formula per audio sample. A signal inlet is `$v1`. A
control-rate number inlet is `$f1`. The control-rate sibling `expr` uses `$f1`
and `$i1` and runs when a message comes in, not every sample. `fexpr~` is the
one that can read past samples (`$x1[-1]` and similar).

| Piece | This project | Pure Data `expr~` |
|-------|----------------|-------------------|
| Formula | one string in `aevalsrc` | one string in an `expr~` box |
| Time | the variable `t` | you pass a phase, or you use `phasor~` outside the box |
| Gate | multiply by `if(...)` or `gt(...)` | multiply by a signal |
| Conditional | `if(cond, a, b)` | `cond ? a : b` |
| Memory inside the formula | `st` / `ld`, ten slots, this sample only | `fexpr~` can read earlier samples |
| Tables | none | `tabread4~`, and `expr~` can index a named array |
| Rates | audio rate only | `expr` is control rate, `expr~` is audio rate |
| The rest of the patch | ffmpeg filters after the formula (`lowpass`, `aecho`, `afir`) | more boxes and wires (`osc~`, `line~`, `lop~`, `delwrite~`) |
| Clock | a rendered file | the audio callback |

A kick like `templates/boom.txt` is the same kind of math as one `expr~` box:
a swept sine, an exponential decay, and a noise click, summed. Pure Data would
usually split that across `phasor~`, `*~`, and `line~` instead of one formula.
Both ways emit one sample stream.

What `expr~` has that `aeval` does not:

- **Sample feedback.** `fexpr~` can build a one-pole filter or a short delay in
  the formula. `aeval` cannot see the previous output sample. A real feedback
  delay here is `aecho` with several taps, not a loop (section 8).
- **Wavetables.** `tabread4~` plays a recorded break or a single cycle. This
  project re-synthesises; it does not load a table.
- **A graph you can hear while you edit it.** Change an inlet and the sound
  changes on the next block. Here you edit markdown and run
  `python -m fftechno audio`.
- **MIDI and messages.** Note-on is a message into the patch. Here a "note" is
  a region of `t` where a gate is 1 (section 10).

What matches closely enough to port a voice by hand: `sin`, `exp`, `if`,
`mod` / `%`, and a multiply-as-gate. A Pure Data `expr~` of
`exp(-6.5*$v1)*sin(2*3.1416*(42*$v1+(150/70)*(1-exp(-70*$v1))))` is the body
of the trip-hop boom, with `$v1` standing in for the time-since-hit `ts`.

### 14.3 Csound score `[ ]`

This is the one literally called "evaluation of expressions" in the Csound
manual, and it is **not** a per-sample synth.

```
i 1  0  1  [110 + 220]
```

Csound reads the score, replaces `[110 + 220]` with `330`, and only then starts
the instrument. The allowed operators are `+ - * / % ^` and parentheses. A macro
such as `[0.3*$CNT.]` is expanded the same way. `~` becomes one random number
between 0 and 1, chosen at load, not a new value every sample.

`sounds.md` is in that family. `synth.py` substitutes `{{key}}` and expands
`{{if_steps(...)}}` into a nested `if` ladder **before** ffmpeg runs. `bar`,
`step`, `beat` and `dur` are filled from `song.md` (`bpm` and `bars`) before that
bake. Do not write those four names in `sounds.md`. After the bake, the ladder is
ordinary `aeval` and runs every sample. Csound's `[ ]` stops at the bake. It never
becomes the oscillator.

So a line like `notes=36.71|49|58.27|55` is the same job as four score p-fields.
The difference is what happens next: Csound starts four notes; this project
leaves one formula running and picks the pitch with `floor(mod(t, ...))`.

### 14.4 Csound orchestra and score

A Csound instrument is a list of opcodes. Each opcode has a rate. `i` means once
per note. `k` means the control rate (often a few thousand times a second). `a`
means every sample. The score is a list of notes. Each note has a start time, a
duration, and p-fields (pitch, amplitude, and anything else the instrument reads
as `p4`, `p5`, ...).

| Piece | This project | Csound |
|-------|----------------|--------|
| Instrument | a file in `templates/` plus one `sounds.md` row | an orchestra instrument (`instr` / `endin`) |
| Note | a step whose gate is 1 | an `i` statement |
| Pitch | a Hertz number in a list | a p-field, often passed through `cpspch` |
| Envelope | `exp(-k*mod(t, step))` inside the formula | `linseg`, `expseg`, `transeg` |
| Time base | one `t` for the whole stem | each note has its own start |
| Rates | audio rate only | `i`, `k`, and `a` |
| Unit generators | the formula, then a short ffmpeg chain | the opcode set (`oscil`, `butterlp`, `delay`, ...) |
| Samples and tables | none | `GEN` routines and `table` / `poscil` |
| Arrangement | `song.md` sections (a gain over a bar range) | the score, plus a mixer instrument |
| When it runs | batch render to a WAV | score render, or a live orchestra |

`song.md` is a coarse score. A section is "these stems at these gains from bar A
to bar B". It is not a note list. The note list, when there is one, is the gate
and `notes` cells in `sounds.md`, compiled into the formula.

The trip-hop sub (`templates/sub.txt`) is the clear example. It holds one pitch
for two bars with `mod(t, cstep)` and a slow `exp` decay. Csound would write one
note of duration two bars, put the pitch in a p-field, and use `expseg` for the
same shape. The waveform can match. The event model does not: there is no
note-on, no per-note init, and no k-rate knob moving under the note.

### 14.5 What to copy, and what not to expect

Copy these ideas freely:

- From `expr~`: one readable formula per voice, gates as multiplies, `if` for a
  step pick. If a formula needs the previous sample, stop and use an ffmpeg
  filter instead of pretending `st`/`ld` are a delay line.
- From Csound's score: keep the numbers in markdown and bake them before render.
  That is `{{key}}` and `if_steps`. Do not expect `[ ]` to run inside `aeval`.
- From Csound's orchestra/score split: `templates/` is the orchestra,
  `sounds.md` is the instrument settings, `song.md` is the arrangement. Adding a
  note is adding a gate and a pitch, not adding an `i` statement.

Do not expect these from ffmpeg eval:

- Live inlets, MIDI, or a patch that changes while it plays (section 10).
- A wavetable or a sampled break (`tabread4~`, Csound `GEN01`).
- A feedback loop inside the formula (`fexpr~`, Csound `delayr`/`delayw`).
- Separate control rate. Every `if` in a 32-step ladder is evaluated every
  sample, which is why a long ladder at 192 kHz is slow (section 11).
- A true note event. Retrigger is `mod(t, period)` returning to zero, or a new
  step on the grid. An arbitrary melody is a list, not a scheduler.
