# SPEC.md - ffmpeg_techno (SRS)

Specification of **ffmpeg_techno**: a **three-minute hardgroove techno track** with
a **granular robotic-speech** voice, a **303 acid** line and an **espeak-ng
"speak to me" vocal**, synthesized by ffmpeg, plus a **black-and-white VapourSynth
+ GLSL** visual that renders images as **ASCII art** with Berlin-techno overlays,
muxed into a final video. Authoritative for the current build and future agents.

---

## 1. Purpose and scope

Produce a ~3-minute hardgroove track (ffmpeg-only synthesis) and an ASCII + B/W
shader visual (VapourSynth + vs-placebo), combined into an MP4.

In scope: expression synthesis, hardgroove kit, 303 acid with a moving filter,
granular speech, espeak vocal, arrangement automation, stereo width, ASCII-image
visual, B/W GLSL overlay, encode/mux, verification.

Out of scope: real-time performance, GUI, MIDI import, sample playback, Python for
the *audio* synthesis (Python is used only for the VapourSynth video).

## 2. Glossary

- **Expression**: ffmpeg `eval` string per sample (`aevalsrc`).
- **Stem**: a single-instrument mono WAV in `output/stems/`.
- **Slot**: one 16th-note cell (0.107143 s). **Section**: an arrangement region.
- **Strip**: the audio data row written into the top of the video frame.
- **Block**: 2 bars; the ASCII visual changes image once per block.

## 3. Global constants

| Name        | Value (s)  | Derivation                        |
|-------------|-----------|-----------------------------------|
| BPM         | 140        | hardgroove                        |
| sample rate | 48000 Hz   | `aevalsrc` `s=`                   |
| beat        | 0.428571   | `60/140`                          |
| sixteenth   | 0.107143   | `beat/4`                          |
| bar         | 1.714286   | `beat*4`                          |
| bars        | 105        | 3 minutes at 140 BPM              |
| duration    | 180        | `bar*105` (`aevalsrc` `d=180`)    |
| master dur. | 180.055    | filter latency padding            |
| channels    | 2 (stereo) | mono stems -> stereo at mix       |
| codec       | pcm_s16le  | final; stems pcm_f32le            |

## 4. Architecture and data flow

```
  filters/<stem>.txt (aevalsrc -> [out])  x9 : kick clap hat ohat perc shaker
                                              bass growl acid
  make_vox.ps1 : espeak-ng -> output/stems/vox.wav
        |                        |
        v                        v
  output/stems/*.wav (mono, f32, 48k, 180s)   -- 10 stems
        |
        v
  filters/mix.txt (10 inputs, section volume automation, sidechain, stereo)   A
        |
        v  output/mix_pre.wav
  filters/master.txt (2-pass loudnorm + limiter -> s16 stereo)               B
        |
        v  output/techno.wav
        |
        +--------------------------------+
                                         v
  visualizer.vpy: ascii/ images -> ASCII art (numpy font) -> YUV444P16
                  -> core.placebo.Shader (B/W Berlin overlay, frame+strip)
                  -> YUV420P8 --vspipe y4m--> ffmpeg -> techno_visualizer.mp4
```

## 5. Build pipeline

1. **Vocal**: `make_vox.ps1` (espeak-ng -> process -> `stems/vox.wav`).
2. **Stem pass** (x9): `-filter_complex_script filters/<s>.txt`.
3. **Mix pass**: 10 `-i` stems + `filters/mix.txt` -> `mix_pre.wav`.
4. **Master pass**: `filters/master.txt` -> `techno.wav`.
5. **Video pass**: `vspipe -c y4m visualizer.vpy - | ffmpeg ...`.

`build.ps1` = phases 1-4; `build_video.ps1` = phase 5 (+ 720p preview).

## 6. Instrument specifications

Notation: `T=0.428571`, `T16=0.107143`, `B=1.714286`, `D=mod(t,T16)`,
`K=floor(mod(t,B)/T16)`.

### 6.1 Kick - `filters/kick.txt`
`0.95*(sin(2*PI*(48*tau+(220/55)*(1-exp(-55*tau))))*exp(-24*tau)+0.4*sin(2*PI*1200*tau)*exp(-420*tau))`,
`tau=mod(t,T)`; `equalizer=f=60:t=q:w=1:g=3`.

### 6.2 Clap - `filters/clap.txt`
`gate=gt(mod(floor(mod(t,B)/T),2),0.5)`;
`0.55*((random(0)*2-1)*exp(-20*tau)+0.5*sin(2*PI*200*tau)*exp(-28*tau))*gate`;
`highpass=900, lowpass=9000`.

### 6.3 Closed hat - `filters/hat.txt`
`0.35*(random(0)*2-1)*exp(-95*D)`; `highpass=7000`.

### 6.4 Offbeat open hat - `filters/ohat.txt`
`to=mod(t+T/2,T)`; `0.4*(random(0)*2-1)*exp(-15*to)*if(lt(to,0.20),1,0)`; `highpass=6500`.

### 6.5 Toms - `filters/perc.txt`
Hits at steps {0,1,3,5,6,8,9,11,13,14}; pitches {196,196,147,175,175,147,131,165,175,147};
`0.7*(sin(2*PI*(P*D+(P*1.1/28)*(1-exp(-28*D))))*exp(-16*D)*G(K))`;
`highpass=110, lowpass=3500, aecho=0.8:0.7:55:0.25`.

### 6.6 Shaker - `filters/shaker.txt`
`0.28*(random(0)*2-1)*exp(-70*D)*if(eq(mod(K,4),2),1,0)`; `highpass=9000`. Offbeat 16ths.

### 6.7 Bass - `filters/bass.txt` (deep)
Rolling saw + sub-octave sine. F map: K0-5=55, K6=110, K7=55, K8-13=49, K14=98, K15=49.
`0.55*(mod(F*D,1)*2-1)*exp(-14*D) + 0.4*sin(2*PI*(F/2)*D)*exp(-10*D)`;
`lowpass=1600, equalizer=f=45:t=q:w=1:g=5, asubboost=cutoff=60:boost=4:dry=0.7:wet=1`.

### 6.8 Granular robotic-speech voice - `filters/growl.txt`
Syllable window `W=if(lt(slot,0.070),sin(PI*slot/0.070)^2,0)`, `slot=mod(t,T16)`.
Grain train `G2=sum_{k=0..3} w2(mod(t+(0.063-k*0.016),0.063)/0.046)`, `w2(x)=if(lt(x,1),sin(PI*x)^2,0)`.
8-slot half-bar phrase pitch `P(K)={1.00,1.19,1.08,-,0.84,0.75,1.12,-}`, gate `G(K)` (rests 3,7).
Carrier `0.6*(mod(65*P*slot+1.5*sin(2*PI*12*t),1)*2-1)+0.4*sin(2*PI*65*P*slot)`;
ring mod `R=0.6+0.4*sin(2*PI*173*t)`; `voice=0.85*W*G2*carrier*R*G`.
Filters: `equalizer` 380/1100/2600, `acrusher=bits=7:mix=0.5:mode=log`,
`asoftclip=type=tanh:threshold=0.7, lowpass=7000`.

### 6.9 303 acid - `filters/acid.txt` (knob twisting)`osc = 0.7*AMP(K)*exp(-5*D)*(mod(ph,1)*2-1)`, `ph = F(K)*(D+(BEND(K)/28)*(1-exp(-28*D)))+0.03*sin(2*PI*5.5*t)`
(vibrato). `F(K)` (Hz): 110,110,220,110,130.81,110,164.81,196,110,110,220,110,174.61,130.81,146.83,110.
`AMP(K)`: accents 1.0 {0,6,8,14}, rests 0 {3,11}, else 0.75. `BEND(K)`: 0.35 {2,7,10,15} else 0.05.
**Filter sweep (the "knob")** is done as a time-automated crossfade of two branches:
`osc` split -> `lowpass=5000` (bright) and `lowpass=350` (dark); each gets a
`volume=...:eval=frame` with `(0.5+0.5*cos(2*PI*t/0.107143))*(0.5+0.5*sin(2*PI*t/16))`
(per-note squelch x a slow 16 s sweep), summed, then `equalizer` 650/1300,
`asoftclip=type=tanh:threshold=0.55`, `acrusher=bits=8:mix=0.35:mode=log`.

### 6.10 Vocal - `make_vox.ps1` -> `output/stems/vox.wav`
`espeak-ng --path <data> -w raw -s 120 -p 25 "speak to me"`, then
`asetrate=18081,aresample=48000,acrusher=bits=6:mix=0.4:mode=log,
asoftclip=type=tanh:threshold=0.6,aecho=0.8:0.7:60|120:0.4|0.25,lowpass=4200,
volume=1.3`, split x6 with `adelay` at 4/28/56/92/126/156 s, `amix`, `apad=whole_dur=180`.

### 6.11 Design rules
- Never exceed 0 dBFS at source. Short decaying envelopes. Quote expressions with
  `'`; **count parentheses** (the outer `N*(` of `perc`/`acid` is the classic miss).

## 7. Mix specification - `filters/mix.txt`

Inputs (order): `0=kick 1=clap 2=hat 3=ohat 4=perc 5=bass 6=growl 7=acid 8=shaker 9=vox`.

**Arrangement** (bar-aligned, seconds): S1=13.714286 (bar 8), S2=54.857143 (bar 32),
S3=68.571429 (bar 40), S4=123.428571 (bar 72), S5=137.142857 (bar 80), S6=168.0
(bar 98), END=180.0. Sections: intro / main1 / break / main2 / break2 / main3 /
outro(12 s fade). Each stem's gain is `volume=volume='<nested if on t>':eval=frame`.
Kick is dropped in breaks.

**Stereo depth**: each stem is panned (`pan=stereo|c0=L*c0|c1=R*c0`); hat L, ohat R,
shaker R, acid slightly R, perc center + `haas`; the sum gets `extrastereo=m=1.3`.
Measured mid ~4 dB above side (solid centre, real width).

```
[bass][growl]amix=inputs=2:normalize=0[low];
[low][key]sidechaincompress=threshold=0.05:ratio=8:attack=5:release=120:makeup=1[lowd];
[lowd][clap][hat][ohat][perc][kickm][acid][shaker][vox]amix=inputs=9:normalize=0[sum];
[sum]extrastereo=m=1.3,acompressor=threshold=0.1:ratio=3:attack=10:release=150[out]
```

## 8. Master specification - `filters/master.txt`

```
[0]loudnorm=I=-14:TP=-1.0:LRA=11:measured_I=-19.54:measured_TP=-3.76:
   measured_LRA=1.80:measured_thresh=-29.57:offset=-0.11:linear=true:print_format=summary,
   alimiter=limit=0.80:level=disabled,
   aresample=48000,aformat=sample_fmts=s16:channel_layouts=stereo[out]
```

Re-measure after any change. `alimiter` **must** set `level=disabled`.

## 9. Output format

`output/techno.wav`: pcm_s16le, 48 000 Hz, 2 ch, ~180.055 s.

## 10. Verification and acceptance criteria

| Check | Command | Result |
|-------|---------|--------|
| Graph validity | `ffmpeg -v error -filter_complex_script filters/*.txt -map "[out]" -f null -` | clean |
| Integrated loudness | `ebur128` | **-14.0 LUFS** |
| True peak | `ebur128=peak=true` | **-1.7 dBFS** |
| Duration/channels | `ffprobe` | ~180.055 s, 48000 Hz, 2 ch |
| Stereo | mid vs side RMS | mid ~4 dB above side |
| Determinism | two renders, `-f framecrc` | identical |

## 11. Determinism

`random(x)` seeded; the shader's `random` is deterministic for a fixed frame sequence.

## 12. Extension guide

- **Tempo**: update `T/T16/B` inline everywhere, `d=`, section times in `mix.txt`,
  `BAR` in `visualizer.vpy`; re-measure loudnorm.
- **Instrument**: add `filters/<name>.txt` -> `[out]`; add to `build.ps1` stems;
  add `-i` to the mix command; wire a label in `mix.txt`.
- **Sections**: edit the `volume` automation in `mix.txt`.
- **Shader / ASCII**: edit `SHADER`, `GRID_W/H`, `RAMP`, `GLYPHS`, `BLOCK` in
  `visualizer.vpy`; iterate with a 1-frame render.

## 13. Risks / limitations

- No user variables in ffmpeg `eval` -> verbose expressions; paren counting is the
  main failure mode.
- `loudnorm` runs at 192 kHz internally; `aresample=48000` required after it.
- ffmpeg filters cannot be automated per-sample, so the 303 filter sweep is a
  frame-rate `volume` crossfade and the perc/tom sweep is baked into the oscillator.
- The ASCII visual is high-entropy, so the 1080p master is large (~258 MB / 3 min).
- vs-placebo `Shader` needs a Vulkan GPU (AMD RX 6800M, ~60 fps).

## 14. File inventory

```
filters/kick clap hat ohat perc shaker bongo rim bass growl acid .txt   instruments
filters/vox.txt (espeak vocal graph)
filters/mix.txt master.txt
make_vox.ps1  build.ps1  visualizer.vpy  build_video.ps1
README.md  SPEC.md  TODO.md
tools/ (espeak-ng, gitignored)   ascii/ (source images, gitignored)
output/techno.wav
output/techno_visualizer.mp4  output/techno_visualizer_720p.mp4
output/stems/*.wav  output/mix_pre.wav  output/logs/*
```

---

## 15. Visualizer (VapourSynth + GLSL vs-placebo) - ASCII, B/W

### 15.1 Purpose
Render a black-and-white visual from `output/techno.wav`: images from `ascii/`
converted to ASCII art, looped at random, with a Berlin-techno overlay (rings,
audio spokes, grid, scanlines, kick glitch, grain) drawn over them.

### 15.2 Environment
VapourSynth R81 + `vs-placebo` (pip) on Python 3.14. `vspipe` pipes y4m. One-off:
`pip install vapoursynth numpy vs-placebo` then `vapoursynth config`.

### 15.3 Pipeline in `visualizer.vpy`
1. **ASCII frames (once).** Decode each needed image with ffmpeg to an 80x45 gray
   grid, map luminance to a ramp `" .:-=+*#%@"`, and draw the glyph with a
   self-contained 5x7 numpy bitmap font (no external deps). Cells are 24x24 px
   (80x45 -> 1920x1080). A deterministic RNG picks one image per **2-bar block**
   (54 blocks); results are cached.
2. **Per-frame data.** `std.ModifyFrame` writes the cached ASCII frame into the
   luma plane (x257) and the audio strip (64 bands + bass + kick + energy) into
   rows 0-3 of a YUV444P16 clip.
3. **Shader.** `core.placebo.Shader(data, shader_s=SHADER, ..., sigmoidize=False,
   linearize=False, matrix=5)`. The GLSL reads `lum = HOOKED_tex(HOOKED_pos).x`
   (the ASCII), the strip (`strip(idx)`), and `frame` (time), and returns
   `vec4(vec3(col),1.0)` (monochrome). Overlay: rings `sin(1/(r+0.12)*3 - t*3 +
   bass*6)`, 8 audio spokes, a grid, `exp(-9r)` core glow, vignette, scanlines,
   grain, and a kick glitch flash. No `iTime` exists in libplacebo custom shaders,
   but vs-placebo exposes `frame` + `random`; `matrix=5` is required so the resize
   has a colours-pace path.
4. **Output.** `core.resize.Bicubic(..., YUV420P8, matrix_in_s="470bg",
   matrix_s="470bg", range_in_s/s="limited")` (`matrix_in_s` needed because the
   input is YUV).

### 15.4 Encode and mux
```
vspipe -c y4m visualizer.vpy - | ffmpeg -f yuv4mpegpipe -i - -i output/techno.wav \
  -c:v libx264 -preset slow -crf 20 -tune film -pix_fmt yuv420p \
  -c:a aac -b:a 192k -shortest -movflags +faststart output/techno_visualizer.mp4
```
Then a 720p preview (`scale=1280:720`, CRF 22).

### 15.5 Parameters and acceptance

| Parameter | Value |
|-----------|-------|
| Resolution / FPS | 1920x1080 / 30 |
| Frames | 5402 (video 180.033 s; audio 180.055 s, `-shortest`) |
| ASCII grid / cell | 80x45 / 24x24 px, ramp 10 chars |
| Image change | 1 random image per 2 bars |
| Render speed | ~60 fps (GPU), ~11 s ASCII precompute at load |
| Deliverables | `techno_visualizer.mp4` (~258 MB), `_720p.mp4` (~128 MB) |

Acceptance: `vspipe -i visualizer.vpy -` reports 1920x1080/30/YUV420P8/5402 frames;
`ffprobe` reports an H.264 1080p30 stream and an AAC stream of ~180 s; sampled frames
show legible ASCII art with the B/W overlay.

### 15.6 Visualizer risks / limitations
- Requires a Vulkan GPU (verified AMD RX 6800M).
- Custom shaders are not raw Shadertoy (hook/uniform model differs); use `frame`
  for time and `HOOKED_tex` for input.
- ASCII + grain is high-entropy -> large file; the 720p preview is the share format.

---

## 16. Quality pass ("closer to Ableton", still no samples)

Applied to raise the sound quality while staying ffmpeg-only:

1. **Oversampling / anti-aliasing.** Every oscillator stem generates at
   evalsrc=...:s=192000, applies its filters, then lowpass=f=19000,aresample=48000.
   This removes harmonics folded back into the audible band by the naive saw/square.
2. **Convolution reverb (synthesized IR, no sample).** output/logs/ir.wav is
   generated from decaying noise ((random(n)*2-1)*exp(-2.2*t)). The mix builds a
   high-passed send ([sum] -> highpass=300 -> volume=0.7) convolved with the IR via
   [send][ir]afir=dry=0:wet=1, then summed back. Real space, no low-end mud.
3. **Layering.** Kick gains a 45 Hz sub-octave and a noise transient; bass gains a
   detuned (*1.006) unison saw.
4. **Per-element saturation.** softclip=type=tanh on kick and bass.
5. **Groove velocity.** Hats/perc/shaker/bongo/rim are multiplied by a golden-angle
   per-step amplitude (0.6+0.4*(0.5+0.5*sin(floor(mod(t,B)/T16)*2.399963))).
6. **Master polish.** High-shelf qualizer=f=9000:t=h:w=0.7:g=1.5 and
   resample=48000:out_sample_fmt=s16:dither_method=triangular_hp (dither).

Result: -14.0 LUFS, -1.9 dBFS true peak. Stems render slower (~6 min total) because
of the 192 kHz generation.

Still not Ableton: there is no true per-voice resonant, automatable filter (the 303
sweep is a bright/dark crossfade), no real swing/humanization beyond velocity, and
the synths are near-single-voice. Closing those fully needs a real synth engine
(still "no samples", since soft synths synthesize rather than play back audio).

---

## 17. Additions (vocals, beeps, resonant 303 filter)

- **Real resonant 24 dB/oct 303 filter.** ffmpeg's lowpass is a 2-pole biquad
  (12 dB/oct) but exposes a Q control (width_type=q) and a runtime-able
  frequency. Two cascaded lowpass=f=1600:width_type=q:width=5 in ilters/acid.txt
  give a genuine resonant 24 dB/oct low-pass, on top of the bright/dark sweep.
  (Cutoff can be automated further via sendcmd/zmq, since frequency carries the
  runtime flag.)
- **Beeps.** ilters/beeps.txt synthesizes a Win-startup-style bell arpeggio
  (C5 E5 G5 C6 E6, two partials incl. an inharmonic 2.76x, decaying) at 192 kHz,
  placed at 0.5 s / 68 s / 137 s with reverb.
- **Vocals.** make_vox.ps1 + ilters/vox.txt render 10 female espeak-ng phrases
  (speak to me, come on, feel it, hard groove, let go, trust me, speak with me,
  lock in, take me higher, hands up), each setrate=23500 (moderate pitch),
  reverb, and placed twice across the track (20 occurrences) via delay + mix.

---

## 18. Latest changes (4 minutes, louder drums, ascii policy, final boost)

- **Duration 4:00 (240 s / 140 bars).** All stems d=240; mix.txt outro boundary
  moved to 228.286 (fade over 11.714 s); ox.txt/eeps.txt pad to 240;
  make_vox.ps1 phrases now placed 3x each (27 hits) across the 4 minutes.
- **Drums louder**: kick/hat x2.55, clap x2.4, ohat x2.25, perc/bongo/rim x1.95,
  shaker x1.875 (multipliers at the front of the drum olume= expressions);
  bass x0.75 and a harder sidechain (threshold 0.03, ratio 12) so the kick cuts.
- **ASCII policy**: the visualizer builds a shuffled playlist of REUSE=3 copies
  of every image in scii/, so **each image appears at least 3 times**; the image
  period = duration/(3*N_images); remaining slots are random. No featured bias.
- **Final volume boost (150%)**: after rendering, the final 	echno_visualizer.mp4
  audio is re-encoded from the clean master at olume=1.5 + limiter=limit=0.80
  (headroom for AAC overshoot) with the video stream copied. Result ~ -9.8 LUFS.
  This post-step does not re-render the video.

---

## 19. Tooling: pure Python (no shell scripts)

The build is driven by the `fftechno` Python package (standard library only);
ffmpeg still performs all synthesis from the graphs in `filters/`.

`
python -m fftechno audio     # vox + IR + stems -> mix -> master
python -m fftechno video     # vspipe | ffmpeg -> MP4 (+720p)
python -m fftechno all       # audio then video
python -m fftechno boost 2.0 # re-level finished MP4s (video copied)
`

Modules: `config` (paths/timing/stem lists/loudness), `proc` (subprocess),
`audio` (IR, stems, mix, 2-pass loudnorm master), `vox` (espeak-ng),
`video` (render/mux, preview, re-level), `cli`.

Changes vs the previous PowerShell build:
- `build.ps1` / `build_video.ps1` / `make_vox.ps1` removed.
- `filters/master.txt` removed: the master graph is generated in
  `fftechno/audio.py` from the loudnorm measurements (no stale values).
- `visualizer.vpy` de-cluttered (unused import, unused constant, updated docs).
- `pyproject.toml` added (metadata + `fftechno` console script).

---

## 20. Programmable arrangement (song.md)

The arrangement is no longer a hand-edited filter graph. It lives in `song.md`:

- scalar keys `bpm`, `bars`, `fade_bars`;
- a **Boosts** table (per-stem gain multiplier);
- a **Sections** table (rows = bar ranges, columns = arranged stems, cells = gain).

`fftechno/arrangement.py` parses it and builds the mix filtergraph: per-stem
`volume=volume='<boost>*<nested if(lt(t,..))>':eval=frame` automation (the final
section fades over `fade_bars`), plus the static routing (panning, kick
side-chain, reverb bus). `fftechno/audio.py` writes it to `output/logs/mix.txt`
and mixes. `filters/mix.txt` was deleted.

The arranged stems are `kick clap hat ohat perc shaker bongo rim bass growl
acid`; `vox` and `beeps` have fixed levels (their placement is in
`filters/vox.txt` / `filters/beeps.txt`). Editing `song.md` and running
`python -m fftechno audio` is all that is needed to rearrange the track.

---

## 21. Markdown-driven instruments (sounds.md)

sounds.md lists instruments as a `name | type | parameters` table;
`python -m fftechno synth` writes `filters/<name>.txt` from generator
functions in `fftechno/synth.py` (registered types: `kick`, `noise`).
Parameters are free-form `key=value` pairs.

Example (a basic 909 4-on-4 kick)::

    | kick909 | kick | amp=0.9, f0=50, sweep=180, rate=50, decay=8, click_freq=1500, click_decay=250, click_amt=0.25 |

Generated graph (verified): a `aevalsrc` whose frequency sweeps 230->50 Hz and
whose amplitude decays, plus a click, anti-aliased (192 kHz -> lowpass -> 48 kHz).

This complements `song.md` (arrangement + mix effects): `sounds.md` defines the
synths, `song.md` the arrangement. The kit's existing `filters/*.txt` remain the
hand-authored versions unless a generated instrument reuses their name.

---

## 22. Command reference

| Command | Effect |
|---------|--------|
| `python -m fftechno audio` | IR + vocals + 12 stems -> mix -> master (`output/techno.wav`) |
| `python -m fftechno synth` | generate `filters/<name>.txt` from `sounds.md` |
| `python -m fftechno video [--boost F] [--static]` | VapourSynth->ffmpeg render + 720p preview (+ optional re-level / frozen frame) |
| `python -m fftechno all [--boost F] [--static]` | audio then video |
| `python -m fftechno boost F` | re-encode the MP4 audio at gain `F` (video copied) |

Package entry points: `fftechno.cli:main` (console script) and `python -m fftechno`.

## 23. Control-surface grammar (song.md, sounds.md)

`song.md` - scalars plus four tables, all parsed by `fftechno/arrangement.py`:

- scalars `bpm`, `bars`, `fade_bars`;
- **Boosts**: `| stem | boost |`;
- **Sections**: `| bars | <stem> | ... |` where every column after `bars` is a stem
  and each cell is a gain; ranges are `start-end` in bars;
- **Pan**: `| stem | mode | left | right |` with `mode` in {center, haas, stereo};
- **Patterns**: `| stem | pattern |` - one bar of 16 steps (`x` hit, `1`-`9`
  velocity, `.` rest), applied as a sample-accurate `aeval` gate on the drum stems;
- **Levels**: `| stem | level |` - fixed level for non-arranged stems (vox, beeps);
- **Effects**: `| effect | value |` - global mix parameters (`reverb_*`,
  `sidechain_*`, `stereo_width`, `bus_*`); all are required (no defaults).

`sounds.md` - **Instruments**: `| name | type | parameters |` with `type` from
`fftechno/synth.py` `GENERATORS` and `parameters` a comma-separated `key=value` list.

Validation rules: section ranges must be contiguous and the last end must equal
`bars`; a Sections column must be a known stem (`MIX_INPUTS` in `config.py`);
an unknown instrument `type` or Effects key raises a clear error.

## 24. Requirements and environment

- **ffmpeg / ffprobe** (gyan.dev full build). Filters used: `aevalsrc`, `sine`,
  `random` (eval), `asubboost`, `asoftclip`, `acrusher`, `equalizer`,
  `highpass`, `lowpass`, `asplit`, `amix`, `pan`, `haas`, `extrastereo`,
  `sidechaincompress`, `acompressor`, `alimiter`, `loudnorm`, `afir`,
  `aresample`, `aformat`, `adelay`, `apad`, `volume` (`eval=frame`).
- **Python 3.10+** - the tooling uses the standard library only (no third-party deps).
- **Video** - a venv with `vapoursynth`, `numpy`, `vs-placebo` (provides
  `vspipe.exe`); `vapoursynth config` once; a **Vulkan GPU** for the GLSL shader.
- **Vocals** - `espeak-ng` extracted under `tools/` (not a system install).

File inventory: `fftechno/*.py`, `song.md`, `sounds.md`, `filters/*.txt`,
`visualizer.vpy`, `pyproject.toml`, `LICENSE`, `README.md`, `SPEC.md`,
`TODO.md`; generated: `output/techno.wav`, `output/techno_visualizer*.mp4`,
`output/stems/*.wav`, `output/logs/*`.

Note: section 7 (the old `filters/mix.txt` description) is superseded by sections
20 and 23 - the mix graph is generated.

## 25. Troubleshooting / FAQ

- **Where are failures logged?** `output/logs/vspipe.log` and
  `output/logs/ffmpeg_video.log` (video); the generated mix graph is written to
  `output/logs/mix.txt` for inspection.
- **Video encoder fails (exit -22)?** Usually a broken frame source - check
  `vspipe.log`. Image decode failures are already tolerated (blank grid fallback).
- **"no path between colorspaces" in the shader step?** `core.placebo.Shader` must
  be called with `matrix=5`; the follow-up resize needs `matrix_in_s`.
- **Loudness numbers look stale?** They can't be - the master graph is generated from
  the measured mix each run (no hard-coded values).
- **No vocals?** Install espeak-ng under `tools/` (see Setup).
- **Can I use a different song length?** Yes - change `bars` (and the section rows).
- **Noncommercial only?** Yes - PolyForm Noncommercial 1.0.0 (see `LICENSE`).

---

## 26. Templating synthesis (no hard-coded values)

Synths and mix routing are fully markdown-driven; the Python holds no default
values.

- `templates/*.txt` - ffmpeg filtergraphs with `{{key}}` placeholders.
- `sounds.md` - global scalars (`sr, dur, lp, osr, bar, step, gold, vbase,
  vamt`) plus an **Instruments** table (`name | template | parameters`).
  `fftechno/synth.py` substitutes the values into the template and writes
  `filters/<name>.txt`; a missing placeholder raises.
- `song.md` - scalars (`bpm, bars, fade_bars`) and the tables **Boosts,
  Sections, Patterns, Pan, Levels, Effects**. `fftechno/arrangement.py` builds
  the mix graph from these alone; the only fixed topology is the mix wiring (kick
  keys the bass+growl low bus, everything sums, a high-passed send runs the
  convolution reverb, then the bus compressor + stereo widener).
- **Patterns** are applied as a sample-accurate `aeval` gate on the drum stems,
  so the 16th-note grid of every drum is editable in markdown.
- **Levels** gives the fixed level of non-arranged stems (vox, beeps).

Section 21's generator-function description is superseded by this templating
approach (`fftechno/synth.py` now only renders templates).
