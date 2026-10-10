# SPEC.md - ffmpeg_techno (SRS)

Specification of **ffmpeg_techno**: a **two-minute hardgroove techno track** with a
**granular robotic-speech** voice and a **303 acid** line, synthesized entirely by
ffmpeg, plus a **VapourSynth + GLSL (vs-placebo) Shadertoy-style visualizer**
combined into a final video. Authoritative for the current build and for future
agents extending it.

---

## 1. Purpose and scope

Produce a ~2-minute hardgroove track with a granular robotic-speech voice and a 303
acid line using only the ffmpeg command line, and render an "insane" GPU shader
visual with VapourSynth + vs-placebo, muxed into an MP4.

In scope: expression synthesis, hardgroove kit, 303 acid, granular speech, 2-minute
arrangement automation, GLSL shader visual, encode/mux, verification.

Out of scope: real-time performance, GUI, MIDI import, sample playback, any Python
for the *audio* synthesis (Python is used only for the VapourSynth video).

## 2. Glossary

- **Expression**: ffmpeg `eval` string per sample (`aevalsrc`). `t`, `n`, `s`,
  `PI`, `sin`, `cos`, `exp`, `mod`, `floor`, `lt`, `gt`, `eq`, `if`, `random(x)`,
  `max`.
- **Stem**: a single-instrument mono WAV in `output/stems/`.
- **Slot**: one 16th-note cell (0.107143 s).
- **Section**: an arrangement region (intro/main/break/main2/outro).
- **Strip**: the audio data row written into the top of the video frame.

## 3. Global constants

| Name        | Value (s)  | Derivation                         |
|-------------|-----------|------------------------------------|
| BPM         | 140        | hardgroove                         |
| sample rate | 48000 Hz   | `aevalsrc` `s=`                    |
| beat        | 0.428571   | `60/140`                           |
| eighth      | 0.214286   | `beat/2`                           |
| sixteenth   | 0.107143   | `beat/4`                           |
| bar         | 1.714286   | `beat*4`                           |
| half-bar    | 0.857143   | voice phrase period                |
| bars        | 70         | 2 minutes at 140 BPM               |
| duration    | 120        | `bar*70` (via `aevalsrc` `d=120`)  |
| master dur. | 120.055    | filter latency padding             |
| channels    | 2 (stereo) | mono stems -> stereo at mix        |
| codec       | pcm_s16le  | final; stems pcm_f32le             |

## 4. Architecture and data flow

```
                    filters/<stem>.txt  (aevalsrc expression -> [out])   x8
  kick clap hat ohat perc bass growl acid
    |    |    |   |    |   |    |    |
    v    v    v   v    v   v    v    v      (one ffmpeg pass each)
  output/stems/*.wav  (mono, f32, 48k, 120s)
                    |
                    v
   filters/mix.txt (8 stems, volume-automation sections, sidechain, bus)  A
                    |
                    v   output/mix_pre.wav
   filters/master.txt (2-pass loudnorm + limiter -> s16 stereo)           B
                    |
                    v   output/techno.wav
                    |
                    +------------------------------+
                                                   v
   visualizer.vpy: numpy strip -> YUV444P16 -> core.placebo.Shader (GLSL)
                   -> numeral overlay -> YUV420P8 --vspipe y4m--> ffmpeg
                    |
                    v   output/techno_visualizer.mp4
```

## 5. Build pipeline

1. **Stem pass** (x8): `-filter_complex_script filters/<s>.txt -map "[out]" -c:a pcm_f32le`.
2. **Mix pass**: 8 `-i` stems + `filters/mix.txt` -> `mix_pre.wav`.
3. **Master pass**: `mix_pre.wav` + `filters/master.txt` -> `techno.wav`.
4. **Video pass**: `vspipe -c y4m visualizer.vpy - | ffmpeg ... -> techno_visualizer.mp4`.

`build.ps1` = phases 1-3; `build_video.ps1` = phase 4 (+ 720p preview).

## 6. Instrument specifications

Notation: `T=0.428571`, `T8=0.214286`, `T16=0.107143`, `B=1.714286`.

### 6.1 Kick - `filters/kick.txt`
`tau=mod(t,T)`;
`0.95*(sin(2*PI*(48*tau+(220/55)*(1-exp(-55*tau))))*exp(-24*tau)+0.4*sin(2*PI*1200*tau)*exp(-420*tau))`;
filter `equalizer=f=60:t=q:w=1:g=3`. 4-on-the-floor.

### 6.2 Clap - `filters/clap.txt`
`gate=gt(mod(floor(mod(t,B)/T),2),0.5)`;
`0.55*((random(0)*2-1)*exp(-20*tau)+0.5*sin(2*PI*200*tau)*exp(-28*tau))*gate`;
`highpass=900, lowpass=9000`. Beats 2 & 4.

### 6.3 Closed hat - `filters/hat.txt`
`0.35*(random(0)*2-1)*exp(-95*mod(t,T16))`; `highpass=7000`. Every 16th.

### 6.4 Offbeat open hat - `filters/ohat.txt`
`to=mod(t+T8,T)`; `0.4*(random(0)*2-1)*exp(-15*to)*if(lt(to,0.20),1,0)`;
`highpass=6500`. On the "&".

### 6.5 Toms/congas - `filters/perc.txt`
`K=floor(mod(t,B)/T16)`, `delta=mod(t,T16)`; hits at steps {1,3,6,9,11,14} with
pitches {196,147,175,131,165,147};
`0.7*(sin(2*PI*(P*delta+(P*1.1/28)*(1-exp(-28*delta))))*exp(-16*delta)*G(K))`;
`highpass=110, lowpass=3500, aecho=0.8:0.7:55:0.25`.

### 6.6 Bass - `filters/bass.txt`
Rolling saw, one note per 16th. `K=floor(mod(t,B)/T16)`.
F map: K0-5=55, K6=110, K7=55, K8-13=49, K14=98, K15=49.
`0.6*(mod(F*mod(t,T16),1)*2-1)*exp(-14*mod(t,T16))`;
`lowpass=1500, equalizer=f=90:t=q:w=1:g=4`.

### 6.7 Granular robotic-speech voice - `filters/growl.txt`
Syllable window `W=if(lt(slot,0.070),sin(PI*slot/0.070)^2,0)`, `slot=mod(t,T16)`.
Grain train `G2=sum_{k=0..3} w2(mod(t+(0.063-k*0.016),0.063)/0.046)`,
`w2(x)=if(lt(x,1),sin(PI*x)^2,0)`. 8-slot half-bar phrase (`K=floor(mod(t,0.857143)/T16)`)
with pitch `P(K)={1.00,1.19,1.08,-,0.84,0.75,1.12,-}` and gate `G(K)` (rests on 3,7).
Carrier `0.6*(mod(65*P*slot+1.5*sin(2*PI*12*t),1)*2-1)+0.4*sin(2*PI*65*P*slot)`;
ring mod `R=0.6+0.4*sin(2*PI*173*t)`; `voice=0.85*W*G2*carrier*R*G`.
Filters: `equalizer=f=380:t=q:w=3:g=8, equalizer=f=1100:t=q:w=3:g=7,
equalizer=f=2600:t=q:w=3:g=6, acrusher=bits=7:mix=0.5:mode=log,
asoftclip=type=tanh:threshold=0.7, lowpass=f=7000`.

### 6.8 303 acid - `filters/acid.txt`
`K=floor(mod(t,B)/T16)`, `delta=mod(t,T16)`. Per-step frequency `F(K)` (Hz):
110,110,220,110,130.81,110,164.81,196,110,110,220,110,174.61,130.81,146.83,110.
Per-step amp `AMP(K)`: accents 1.0 on {0,6,8,14}, rests 0.0 on {3,11}, else 0.75.
Per-step bend `BEND(K)`: 0.35 on {2,7,10,15} else 0.05 (pitch squawk).
Phase `ph=F*(delta+(BEND/28)*(1-exp(-28*delta)))`; `sig=0.7*AMP*(mod(ph,1)*2-1)`.
Filters: `asoftclip=type=tanh:threshold=0.6, equalizer=f=700:t=q:w=2:g=10,
equalizer=f=1400:t=q:w=3:g=6, lowpass=f=4500, acrusher=bits=8:mix=0.3:mode=log`.
The 303's resonant filter sweep is baked into the oscillator's per-note bend +
resonant EQ peaks (ffmpeg filters cannot be automated per-sample).

### 6.9 Design rules
- Never let a stem exceed 0 dBFS; fix at source.
- Short decaying envelopes so `mod` gating needs no explicit gate.
- Quote expressions with `'`; keep parentheses balanced (`acid`/`perc` tom sweeps
  are the easiest places to miscount).

## 7. Mix specification - `filters/mix.txt`

Inputs (order): `0=kick 1=clap 2=hat 3=ohat 4=perc 5=bass 6=growl 7=acid`.

Arrangement sections (bar-aligned): S1=13.714286 (bar 8), S2=41.142857 (bar 24),
S3=54.857143 (bar 32), S4=96.0 (bar 56), END=120.0. Each stem's `volume` is
automated with `eval=frame` and `t`, e.g. kick:

```
[0]volume=volume='if(lt(t,13.714286),0.9,if(lt(t,41.142857),1.0,
   if(lt(t,54.857143),0.0,if(lt(t,96.0),1.0,max(0,1-(t-96.0)/24.0)))))':eval=frame[kickv];
[kickv]asplit=2[kick][key];
```

Sections: intro (kick+hat+acid), main1 (add bass/clap/ohat/perc/growl), break (kick
dropped), main2 (all), outro (24 s fade). Then:

```
[bass][growl]amix=inputs=2:normalize=0[low];
[low][key]sidechaincompress=threshold=0.05:ratio=8:attack=5:release=120:makeup=1[lowd];
[lowd][clap][hat][ohat][perc][kick][acid]amix=inputs=7:normalize=0[sum];
[sum]aformat=channel_layouts=stereo,acompressor=threshold=0.1:ratio=3:attack=10:release=150[out]
```

## 8. Master specification - `filters/master.txt`

Two-pass linear loudness normalisation + true-peak limiter.

```
[0]loudnorm=I=-14:TP=-1.0:LRA=11:measured_I=-19.07:measured_TP=-5.68:
   measured_LRA=2.10:measured_thresh=-29.23:offset=0.07:linear=true:print_format=summary,
   alimiter=limit=0.80:level=disabled,
   aresample=48000,aformat=sample_fmts=s16:channel_layouts=stereo[out]
```

Re-measure after any tempo/pattern change. `alimiter` **must** set
`level=disabled` (default auto-level boosts over the ceiling).

## 9. Output format

`output/techno.wav`: pcm_s16le, 48 000 Hz, 2 ch, ~120.055 s.

## 10. Verification and acceptance criteria

| Check | Command | Result |
|-------|---------|--------|
| Graph validity | `ffmpeg -v error -filter_complex_script filters/*.txt -map "[out]" -f null -` | clean |
| Integrated loudness | `ebur128` | **-14.0 LUFS** |
| True peak | `ebur128=peak=true` | **-1.6 dBFS** |
| Duration/channels | `ffprobe` | ~120.055 s, 48000 Hz, 2 ch |
| Arrangement | `showwavespic` | sparse intro, dense body, fade outro |
| Determinism | two renders, `-f framecrc` | identical |
| Voice | `showwavespic` of growl | discrete syllable bursts with rests |

Acceptance for future edits: all rows hold; voice keeps grains + pitch contour +
ring mod + formant EQ; acid keeps per-step pitch + accents + bend.

## 11. Determinism

`random(x)` is seeded and deterministic for a fixed sample count. The shader uses
`random` per frame (vs-placebo) - still deterministic for a fixed frame sequence.

## 12. Extension guide

- **Tempo**: update `T/T8/T16/B` inline everywhere, `d=` durations, section times
  in `mix.txt`, and `BAR` in `visualizer.vpy`; re-measure loudnorm.
- **Instrument**: add `filters/<name>.txt` ending in `[out]`; add to `build.ps1`
  stems, add `-i output/stems/<name>.wav` to the mix command, wire a label in
  `mix.txt`.
- **Sections**: edit the `volume` automation expressions in `mix.txt`.
- **Shader**: edit `SHADER` in `visualizer.vpy`; iterate with a 1-frame render.

## 13. Risks / limitations

- No user variables in ffmpeg `eval` -> verbose expressions.
- `loudnorm` runs at 192 kHz internally; `aresample=48000` required after it.
- ffmpeg filters cannot be automated per-sample, so the 303 filter sweep is
  approximated in the oscillator domain.
- The 1080p master is large (~168 MB for 2 min) because of grain/neon gradients.

## 14. File inventory

```
filters/kick.txt clap.txt hat.txt ohat.txt perc.txt bass.txt growl.txt acid.txt
filters/mix.txt master.txt
build.ps1  visualizer.vpy  build_video.ps1
README.md  SPEC.md  TODO.md
output/techno.wav
output/techno_visualizer.mp4  output/techno_visualizer_720p.mp4
output/stems/*.wav  output/mix_pre.wav  output/logs/*
```

---

## 15. Visualizer (VapourSynth + GLSL vs-placebo) and final video

### 15.1 Purpose
Render an "insane" GPU-shader visual from `output/techno.wav` and mux it into the
final MP4. Aesthetic: a rotating kaleidoscopic neon acid tunnel with a glowing core,
audio-reactive spokes/rays, kick glitches, grain, and a countdown numeral.

### 15.2 Environment
VapourSynth R81 + `vs-placebo` (pip wheels) on Python 3.14. This ffmpeg has no
VapourSynth input, so `vspipe` pipes y4m. One-off: `pip install vapoursynth numpy
vs-placebo` then `vapoursynth config`.

### 15.3 Pipeline in `visualizer.vpy`
1. **Audio strip.** numpy STFT -> 64 band levels + bass + kick + energy per frame.
   Each frame writes 67 values x 24 px into rows 0-3 of a YUV444P16 clip
   (`std.ModifyFrame`), value -> luma 0..65535.
2. **Shader.** `core.placebo.Shader(data, shader_s=SHADER, width, height,
   sigmoidize=False, linearize=False, matrix=5)`. The shader (mpv/libplacebo
   syntax) generates the whole visual. Key facts:
   - libplacebo custom shaders have no `iTime`, but **vs-placebo exposes `frame`**
     and `random` uniforms -> animate on `float(frame)/FPS`.
   - Audio reactivity: `HOOKED_tex(vec2((idx*24+12)/1920, 1.5/1080)).x` reads the
     strip.
   - `sigmoidize/linearize=False` preserves the raw strip values.
   - The shader output must declare a valid matrix (`matrix=5`), else resize fails
     with "no path between colorspaces".
3. **Numeral overlay.** `std.ModifyFrame` draws two 7-segment digits (tens/ones of
   `TOTAL_BARS - bar_index`, i.e. 70 -> 1) additively on the luma plane with
   clipping.
4. **Output.** `core.resize.Bicubic(..., YUV420P8, matrix_in_s="470bg",
   matrix_s="470bg", range_in_s/s="limited")`. `matrix_in_s` is required here
   (input is YUV); do not set it for RGB->YUV.

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
| Frames | 3602 (video 120.033 s; audio 120.055 s, `-shortest`) |
| Video codec | H.264 CRF 20 `-tune film`, yuv420p |
| Audio codec | AAC 192 kbps |
| Render speed | ~60 fps (GPU shader) |
| Deliverables | `techno_visualizer.mp4` (~168 MB), `_720p.mp4` (~79 MB) |

Acceptance: `vspipe -i visualizer.vpy -` reports 1920x1080/30/YUV420P8/3602 frames;
`ffprobe` reports an H.264 1080p30 stream and an AAC stream of ~120 s; sampled frames
show the tunnel and the numeral decrementing once per bar.

### 15.6 Visualizer risks / limitations
- vs-placebo `Shader` requires a Vulkan GPU; verified on an AMD RX 6800M.
- Custom shaders are not raw Shadertoy (different hook/uniform model); a Shadertoy
  shader must be adapted (use `frame` for time, `HOOKED_tex` for input).
- Shader output is YUV444P16 and must carry a valid matrix for the follow-up resize.
