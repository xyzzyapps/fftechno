# Sound design in the templates

This is a guide to the synthesis techniques used by the non-sample instruments in
`templates/`. It is about sound design, not sequencing or mixing; those are covered
in [SONG_EXPLANATION.md](SONG_EXPLANATION.md).

Every synth template follows the same shape:

```text
aevalsrc expression  ->  filters  ->  resample  ->  [out]
```

The source is usually mono. Stereo comes later from panning, sends and the mix bus.

## The basic building blocks

### Oscillators

- **Sine:** `sin(2*PI*f*t)`
- **Saw:** `mod(f*t,1)*2-1`
- **Square / pulse:** `gt(mod(f*t,1),0.5)*2-1`
- **Noise:** `random(0)*2-1`, `random(1)*2-1`, ...

Noise is deterministic for a fixed ffmpeg build. It is the main ingredient in hats,
snares, claps, shakers and breath sounds.

### Envelopes

A percussive envelope usually retriggers on a grid:

```text
exp(-decay * mod(t, step))
```

A longer note uses an attack/sustain/decay/release shape:

```text
(1-exp(-atk*phase)) * (sus + (1-sus)*exp(-dec*phase))
* (1-exp(-rel*(length-phase)))
```

The `phase` is usually `mod(t, step)`, `mod(t, beat)` or `mod(t, bar)`, so the
envelope restarts at the right musical interval.

### Pitch contours

A falling pitch gives a drum its “hit”:

```text
f0*t + (sweep/rate)*(1-exp(-rate*phase))
```

A short, fast sweep is a click. A slower sweep is a tom or a kick.

### Gating and velocity

Step lists turn an envelope into a pattern:

```text
gate     = if_steps(gates; grid; 0)
velocity = if_steps(vel;   grid; 1)
```

The gate decides whether a hit exists; velocity scales its level.

### Filtering and saturation

Common filters:

- `highpass` - removes rumble or thickness.
- `lowpass` - removes harshness; a low cutoff makes a darker sound.
- `equalizer` - boosts or cuts one band.
- `asoftclip=type=tanh` - adds density and prevents hard clipping.
- `acrusher` - bit reduction for a dusty or lo-fi texture.
- `aecho` / `aphaser` / `tremolo` / `chorus` / `vibrato` - movement and space.

Almost every template ends with a final `lowpass=f={{lp}}` and
`aresample={{osr}}` (usually 48 kHz).

## Drums

### Kick (`kick.txt`, `kick_trip.txt`, `boom.txt`)

A kick is layered from four short events:

1. **Body:** a sine whose pitch falls quickly.
2. **Click:** a short high sine or noise burst.
3. **Sub:** a low sine that extends the tail.
4. **Noise:** a very short noise transient.

The template adds an EQ around the fundamental, a soft clip, and a final low-pass.
`kick_trip` adds a gate list so the kick can be programmed per step. `boom` is the
same idea with a longer, deeper tail.

### Snare (`snare.txt`)

A snare is two tuned sines plus noise:

- two body tones (`f1`, `f2`) with a medium decay,
- a noise layer with a shorter decay,
- a high-pass to remove rumble,
- a low-pass to tame the noise.

`snare` can be gated per step. `snarefill` reuses the same template with a denser
gate list to make rolls and fills.

### Clap (`clap.txt`)

A clap is a burst of noise plus a short tonal body. The template uses a fast noise
decay and a second, slower tone decay. A beat gate restricts it to the backbeat.

### Hats (`hat.txt`, `hat_step.txt`, `ohat.txt`, `ohat_dyn.txt`)

A hat is filtered noise with a very short envelope:

```text
noise * exp(-decay * phase) -> highpass -> lowpass
```

- `hat.txt` uses a golden-ratio velocity variation.
- `hat_step.txt` uses explicit `gates` and `vel` lists.
- `ohat.txt` opens a window on the offbeat with `off` and `win`.
- `ohat_dyn.txt` varies both decay and velocity per hit from golden-ratio
  sequences. It is deterministic but does not settle into a one-bar loop.

### Ride, crash and shaker

- **Ride:** several inharmonic sines plus noise, with a longer decay.
- **Crash:** a noise burst plus a few high tones, repeating every `period`.
- **Shaker:** short filtered noise with a gate and a small velocity curve.

### Toms and congas (`tom.txt`, `conga.txt`)

Both use a tuned sine with a pitch sweep. `conga` adds a short noise “slap”.
`pitches` selects the drum pitch per step, and `gates` selects which steps hit.
A short `aecho` adds room.

### Rim (`rim.txt`)

A rim is a very short high sine plus a noise click, with a fast decay and a
high-pass. It is closer to a click than a drum.

### Breakbeat (`breakbeat.txt`, `break_synth.txt`, `break_sp.txt`)

These templates synthesize a whole break from separate kick, snare and hat
components inside one expression. Each component has its own gate and velocity
list. `break_sp` adds an open hat and a swing phase; `breakbeat` adds a chopped
amplitude modulation.

## Bass

### `bass.txt` and `bass_gate.txt`

A simple bass layers:

- a saw for the body,
- a sine an octave below for weight,
- a detuned saw for width.

It then uses a resonant low-pass, an EQ, `asubboost` for sub weight, a soft clip and
a final low-pass. `bass_gate` adds a per-step gate so the bass can be rhythmic.

### `bass_rock.txt`

A rock bass is a saw plus a sub sine, with a high-pass, a resonant low-pass, an EQ
and a tanh clip. It is simpler and more forward than the electronic bass.

### `reese.txt`

A reese is two detuned squares plus a sub sine. The character comes from:

- a high-pass,
- two low-passes,
- a resonant EQ peak at the cutoff,
- a tanh clip.

The result is a wide, moving bass without needing a second oscillator track.

## Leads and melodic voices

### `lead_pwm.txt`

A PWM lead is a pulse wave whose width is modulated by an LFO:

```text
gt(mod(f*t,1), pw_base + pw_amt*sin(2*PI*pw_f*t))
```

Two detuned copies thicken it. A high-pass, tanh clip and low-pass finish it.

### `lead_fm.txt`

A two-operator FM lead:

```text
sin(2*PI*fc*t + fm_amt*sin(2*PI*fm*t))
```

The modulation index and ratio set the brightness and metallic character. A phaser,
high-pass, tanh clip and low-pass shape it.

### `acid.txt` and `acid_303.txt`

The 303-style voice is a saw with per-step accents and pitch bends. It is split into
a bright and a dark path, crossfaded with a cosine LFO, then sent through a resonant
low-pass, EQ, bitcrush and soft clip. This is the most “alive” template: the accents
and bends are part of the note list, not a separate effect.

`acid_303.txt` is the oldschool variant used by `oldschool_acid`. It adds a per-step
gate plus a short attack before the decay, so the 303 phrase has rests and a more
articulated envelope instead of running continuously. Its `acidgrid` is 32 steps
(two bars), so the line varies over two bars before repeating.

### `sax.txt` and `horn.txt`

Both are saw-based voices with:

- a detuned second saw,
- a breath-noise layer,
- vibrato,
- two EQ bands,
- a soft clip and low-pass.

The difference is in the envelope, vibrato and EQ settings. They are examples of
how far a saw plus noise can be pushed.

### `bell.txt`

A bell is a sine with FM and a fast decay, followed by a high-pass, soft clip,
low-pass and echo. The inharmonic ratio is what makes it sound like a bell rather
than a pure tone.

## Keys, pads and chords

### `ep.txt` and `rhodes.txt`

Both are FM electric pianos. Each note has:

- a carrier sine,
- an FM modulator with a fast decay,
- a second and third voice at different levels.

The difference is the voicing and envelope. `ep` is shorter and dustier; `rhodes` is
fuller. Both use a high-pass, EQ, soft clip, bitcrush and low-pass.

### `pad.txt` and `strings.txt`

A pad is a detuned chord of saws with a slow tremolo and a slow attack. `strings`
adds a longer attack and a second detuned voice. Both use a high-pass and low-pass
to sit behind the mix.

### `stab.txt`

A stab is a short detuned chord with a fast decay. It is the same chord idea as a
pad, but the envelope is short and the filter is more open.

### `organ.txt`

An organ is a stack of square “drawbars” at different octaves, with tremolo and
chorus. A high-pass and low-pass remove the extremes.

## Guitars

### `guitar_fuzz.txt`

A fuzz guitar is a saw-based power chord:

- root,
- octave,
- fifth,
- two detuned copies.

It goes through a high-pass, tanh fuzz, cabinet low-pass, EQ, phaser and a short
echo. The tanh is the amp; the low-pass is the speaker.

### `guitar_lead.txt` and `guitar_wah.txt`

Both are single-note saw leads with a sub and an octave. `guitar_lead` uses vibrato;
`guitar_wah` uses a phaser for the wah effect. Both use a high-pass, tanh, low-pass
and EQ. The lead deliberately has no echo: the global reverb supplies the space.

## Continuous movement (LFOs)

`lowpass=f` **cannot** be time-varying in ffmpeg - it rejects a `t` expression. A
moving filter is therefore built by copying the source, filtering each copy at a
fixed cutoff, and crossfading the copies with sine LFOs on `volume`.

`templates/acid_lfo.txt` does this with four bands (320 / 700 / 1500 / 3200 Hz), each
faded by its own slow sine:

```text
volume = w_a + w_b * sin(2*PI*t / r + p)
```

- `r` - the LFO period in seconds.
- `p` - a phase offset that staggers the bands.
- `w_a` / `w_b` - the centre level and depth.

Using four different periods (7.3, 11.9, 17.3, 23.7 s) means the bands never line
up, so the timbre drifts continuously. A fifth LFO breathes the overall level.

This is the ffmpeg equivalent of slowly turning a cutoff and resonance knob:
`volume=...:eval=frame` is genuinely continuous, and the result is deterministic.

## Space and movement

The templates use a small set of movement tools:

- `aecho` - short slap or multi-tap delay.
- `aphaser` - sweeping phase.
- `tremolo` - amplitude movement.
- `chorus` - detuned doubling.
- `vibrato` - pitch movement.
- `asubboost` - low-end weight.
- `acrusher` - lo-fi dust.

The mix bus adds the larger space: a convolution reverb (`afir`), stereo width and
bus compression. Per-stem reverb sends are not implemented yet; the global send is
the current approach.

## A practical sound-design workflow

When making a new template:

1. **Choose the excitation:** sine, saw, square or noise.
2. **Choose the envelope:** click, hit, pluck, pad or drone.
3. **Add pitch movement:** a fast drop for drums, vibrato for leads.
4. **Filter:** high-pass the rumble, low-pass the harshness, EQ the character.
5. **Saturate:** tanh for density, crusher for dust.
6. **Add movement:** echo, phaser, tremolo or chorus.
7. **Gain-stage:** set `amp`, then use a soft clip and final low-pass.
8. **Resample:** write the template at the intended `sr`, then resample to `osr`.

The sound should still make sense with the effects bypassed. The filters and effects
are there to shape a good source, not to rescue a weak one.