"""visualizer.vpy - VapourSynth + GLSL (vs-placebo) visualizer for output/techno.wav.

Aesthetic: an "insane" time-driven Shadertoy-style procedural scene - a
kaleidoscopic neon acid tunnel with a glowing core, audio-reactive spokes and
rays, kick glitches and film grain - with a two-digit countdown numeral
overlaid (70 bars counting down), i.e. film-leader meets Berlin acid.

Pipeline
--------
1. numpy STFT -> per-frame band levels; a small data strip (67 values x 24 px) is
   written into the top rows of a YUV444P16 clip each frame.
2. core.placebo.Shader runs a GLSL (mpv/libplacebo syntax) shader. libplacebo
   custom shaders have no iTime, but vs-placebo exposes the `frame` uniform, so
   the shader animates on float(frame)/FPS. It reads the data strip via
   HOOKED_tex for audio reactivity. The shader is the whole visual.
3. A countdown numeral is drawn over the shader output on the luma plane, then
   the clip is converted to YUV420P8 for y4m piping.

Run:  .venv\\Scripts\\vspipe.exe -c y4m visualizer.vpy - | ffmpeg -f yuv4mpegpipe -i - ...
Info: .venv\\Scripts\\vspipe.exe -i visualizer.vpy -
"""

import ctypes
import math
import wave

import numpy as np
import vapoursynth as vs

core = vs.core

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
AUDIO_PATH = "output/techno.wav"
W, H, FPS = 1920, 1080, 30
NBARS = 64
BAR = 60.0 / 140.0 * 4.0            # bar length in seconds (1.7142857)
CELL = 24                           # strip: pixels per value
AUX_X = NBARS * CELL                # first aux value x-offset
STRIP_ROWS = 4
CENTRE = (W * 0.5, H * 0.5)


# ---------------------------------------------------------------------------
# GLSL shader (mpv / libplacebo syntax; `frame` + `random` are provided by
# vs-placebo, HOOKED_tex samples the input strip for audio reactivity)
# ---------------------------------------------------------------------------
SHADER = """
//!HOOK MAIN
//!BIND HOOKED
//!DESC berlin acid tunnel

#define FPS 30.0

float strip(float idx){
    return HOOKED_tex(vec2((idx*24.0+12.0)/1920.0, 1.5/1080.0)).x;
}
float band(float b){ return strip(b); }
float aux(float i){ return strip(64.0+i); }

vec3 pal(float x){
    return mix(vec3(0.10,0.02,0.28), vec3(0.95,0.25,0.85),
               0.5+0.5*sin(6.28318*x))
         + vec3(0.0,0.25,0.30)*(0.5+0.5*sin(6.28318*(x+0.25)));
}
float hash(float n){ return fract(sin(n)*43758.5453); }

vec4 hook(){
    float t = float(frame)/FPS;
    float bass = aux(0.0);
    float kick = aux(1.0);
    float energy = aux(2.0);
    vec2 res = target_size;
    vec2 uv = (HOOKED_pos*res - 0.5*res)/res.y;

    float r = length(uv);
    float ang = atan(uv.y, uv.x) + t*0.15;
    float seg = 8.0;
    float ka = abs(mod(ang, 6.28318/seg) - 3.14159/seg);

    // perspective tunnel coordinates
    float depth = 1.0/(r + 0.15) + t*1.2 + bass*2.0;
    vec2 tp = vec2(ka*3.0, depth);
    float gx = smoothstep(0.90, 1.0, abs(fract(tp.x)-0.5)*2.0);
    float gy = smoothstep(0.85, 1.0, abs(fract(tp.y)-0.5)*2.0);
    float grid = max(gx, gy);

    vec3 col = pal(depth*0.05 + bass*0.2) * (0.10 + grid*1.3);
    col += exp(-9.0*r) * vec3(1.0,0.60,0.15) * (0.40 + kick*1.5);

    float spokes = 0.0;
    for(int i=0;i<8;i++){
        spokes += band(float(i)*8.0) * exp(-22.0*abs(ka - 0.12*float(i)));
    }
    col += pal(0.6 + 0.2*energy) * spokes * 0.7;
    col += pal(0.4 + r*0.3) * smoothstep(0.9, 0.0, r) * (0.10 + energy*0.6);

    if(step(0.75, kick) > 0.5){
        col = col.gbr;
        col += (hash(floor(t*30.0)) - 0.5)*0.2;
    }

    col = pow(clamp(col, 0.0, 1.0), vec3(1.3));
    col *= 1.0 - 0.7*r;
    col += (random - 0.5)*0.05;
    return vec4(col, 1.0);
}
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def plane_u16(frame, p):
    """Writable numpy uint16 view of a 16-bit plane (R81 API)."""
    sw, sh = frame.format.subsampling_w, frame.format.subsampling_h
    pw, ph = frame.width >> sw, frame.height >> sh
    stride = frame.get_stride(p)          # bytes
    ptr = frame.get_write_ptr(p).value
    buf = (ctypes.c_uint8 * (stride * ph)).from_address(ptr)
    return np.frombuffer(buf, dtype=np.uint16).reshape(ph, stride // 2)[:, :pw]


SEG = {0: "abcdef", 1: "bc", 2: "abged", 3: "abgcd", 4: "fgbc",
       5: "afgcd", 6: "afgecd", 7: "abc", 8: "abcdefg", 9: "abcdfg"}


def draw_digit_luma(luma, d, cx, cy, w, h, th, value):
    """Additively draw a 7-segment numeral into a uint16 luma plane."""
    left, top = int(cx - w / 2), int(cy - h / 2)
    right, bottom, mid = left + int(w), top + int(h), top + int(h / 2)
    segs = {
        "a": (left + th, top, right - th, top + th),
        "b": (right - th, top + th, right, mid),
        "c": (right - th, mid, right, bottom - th),
        "d": (left + th, bottom - th, right - th, bottom),
        "e": (left, mid, left + th, bottom - th),
        "f": (left, top + th, left + th, mid),
        "g": (left + th, mid - th // 2, right - th, mid + th // 2),
    }
    for name, (x0, y0, x1, y1) in segs.items():
        if name not in SEG[d]:
            continue
        for pad, frac in ((0, 1.0), (8, 0.4), (18, 0.15)):
            add = int(value * frac)
            reg = luma[max(0, y0 - pad):min(H, y1 + pad),
                       max(0, x0 - pad):min(W, x1 + pad)]
            reg[:] = np.clip(reg.astype(np.int32) + add, 0, 65535).astype(np.uint16)


# ---------------------------------------------------------------------------
# Audio analysis
# ---------------------------------------------------------------------------
def analyse(path):
    with wave.open(path, "rb") as wf:
        sr, nch, nframes = wf.getframerate(), wf.getnchannels(), wf.getnframes()
        raw = wf.readframes(nframes)
    data = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    data = data.reshape(-1, nch)
    mono = data.mean(axis=1)

    duration = nframes / sr
    n_frames = int(math.ceil(duration * FPS))
    hop = sr // FPS
    win = 2048
    window = np.hanning(win).astype(np.float32)

    freqs = np.fft.rfftfreq(win, 1.0 / sr)
    edges = np.geomspace(28.0, 16000.0, NBARS + 1)
    band_idx = [np.where((freqs >= edges[b]) & (freqs < edges[b + 1]))[0]
                for b in range(NBARS)]
    low_idx = np.where(freqs < 120.0)[0]

    spec_db = np.zeros((n_frames, NBARS), np.float32)
    bass_db = np.zeros(n_frames, np.float32)
    energy = np.zeros(n_frames, np.float32)
    for i in range(n_frames):
        s = i * hop
        seg = mono[s:s + win]
        if seg.shape[0] < win:
            seg = np.pad(seg, (0, win - seg.shape[0]))
        mag = np.abs(np.fft.rfft(seg * window)) + 1e-7
        for b in range(NBARS):
            idx = band_idx[b]
            spec_db[i, b] = 20.0 * np.log10(mag[idx].mean()) if idx.size else -120.0
        bass_db[i] = 20.0 * np.log10(mag[low_idx].mean())
        energy[i] = np.sqrt(np.mean(seg ** 2)) + 1e-9

    def norm(db, lo_pc, hi_pc):
        lo, hi = np.percentile(db, lo_pc), np.percentile(db, hi_pc)
        return np.clip((db - lo) / (hi - lo + 1e-6), 0.0, 1.0)

    level = norm(spec_db, 25, 99.7) ** 1.25
    smooth = np.zeros_like(level)
    prev = np.zeros(NBARS, np.float32)
    for i in range(n_frames):
        prev = np.where(level[i] > prev,
                        prev + (level[i] - prev) * 0.55,
                        prev * 0.80)
        smooth[i] = prev

    bass = norm(bass_db, 10, 99)
    kick = np.zeros(n_frames, np.float32)
    k = 0.0
    for i in range(n_frames):
        k = max(bass[i], k * (1.0 - 1.0 / (FPS * 0.25)))
        kick[i] = k
    en = np.clip(energy / (np.percentile(energy, 99) + 1e-9), 0.0, 1.0)

    return dict(duration=duration, n_frames=n_frames, level=smooth,
                bass=bass, kick=kick, energy=en)


A = analyse(AUDIO_PATH)
NF = A["n_frames"]
TOTAL_BARS = int(math.ceil(A["duration"] / BAR))


# ---------------------------------------------------------------------------
# Data clip: YUV444P16 with the audio strip in the top rows
# ---------------------------------------------------------------------------
def build_data(n, f):
    fc = f.copy()
    luma = plane_u16(fc, 0)
    vals = np.concatenate([A["level"][min(n, NF - 1)],
                           [A["bass"][min(n, NF - 1)],
                            A["kick"][min(n, NF - 1)],
                            A["energy"][min(n, NF - 1)]]]).astype(np.float32)
    for i, v in enumerate(vals):
        x0 = i * CELL
        luma[0:STRIP_ROWS, x0:x0 + CELL] = np.uint16(np.clip(v, 0, 1) * 65535)
    return fc


blank = core.std.BlankClip(width=W, height=H, format=vs.YUV444P16,
                           length=NF, fpsnum=FPS, fpsden=1)
data = core.std.ModifyFrame(blank, blank, build_data)

# ---------------------------------------------------------------------------
# GLSL shader (the whole visual) -> YUV444P16
# ---------------------------------------------------------------------------
shaded = core.placebo.Shader(data, shader_s=SHADER, width=W, height=H,
                             sigmoidize=False, linearize=False, matrix=5)


# ---------------------------------------------------------------------------
# Countdown numeral overlay on the luma plane
# ---------------------------------------------------------------------------
def overlay(n, f):
    fc = f.copy()
    luma = plane_u16(fc, 0)
    bar_index = int((n / FPS) / BAR)
    number = max(1, TOTAL_BARS - bar_index)
    tens, ones = (number // 10) % 10, number % 10
    draw_digit_luma(luma, tens, CENTRE[0] - 130, CENTRE[1], 200, 340, 36, 32000)
    draw_digit_luma(luma, ones, CENTRE[0] + 130, CENTRE[1], 200, 340, 36, 32000)
    return fc


with_num = core.std.ModifyFrame(shaded, shaded, overlay)
clip = core.resize.Bicubic(with_num, format=vs.YUV420P8, matrix_in_s="470bg",
                           matrix_s="470bg", range_in_s="limited",
                           range_s="limited")
clip.set_output()
