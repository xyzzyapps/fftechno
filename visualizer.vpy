"""visualizer.vpy - VapourSynth audio-reactive visualizer for output/techno.wav.

Aesthetic: dark Berlin warehouse techno - near-black concrete, a receding
perspective floor grid, hypnotic concentric rings pulsing on the bass, neon
spectrum tubes rising off the floor with a wet-floor reflection, an oscilloscope
trace, kick-driven strobes and chromatic glitch, scanlines and film grain.

Run (video only, piped to ffmpeg):
    .venv\\Scripts\\vspipe.exe -c y4m visualizer.vpy - | ffmpeg -f yuv4mpegpipe -i - ...
Or inspect:  .venv\\Scripts\\vspipe.exe -i visualizer.vpy -

Design notes
------------
- Audio analysis happens once at script load (numpy STFT -> per-frame band
  levels). Frames are drawn in pure numpy inside a std.ModifyFrame callback so
  the whole visual is deterministic and reproducible.
- In VapourSynth R81 the frame planes are read-only memoryviews; writing uses
  frame.copy() + get_write_ptr(plane).value + get_stride(plane) with ctypes.
- The clip is authored as planar RGB24 (planes = G, B, R) and converted to
  YUV420P8 by the built-in resize for y4m piping.
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
HORIZON_Y = int(H * 0.62)          # floor meets the wall here
CENTRE = (W * 0.5, H * 0.40)       # rings centre
BG = np.array([0.018, 0.020, 0.030], np.float32)   # concrete black, cool tint


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def hsv2rgb(h, s, v):
    """Vectorised HSV -> RGB, h/s/v in [0,1]. Returns array shaped (...,3)."""
    h = np.mod(h, 1.0)
    i = np.floor(h * 6.0).astype(np.int32)
    f = h * 6.0 - i
    i = np.mod(i, 6)
    p, q, t = v * (1 - s), v * (1 - f * s), v * (1 - (1 - f) * s)
    one = np.ones_like(f)
    r = np.select([i == 0, i == 1, i == 2, i == 3, i == 4, i == 5],
                  [v * one, q, p, p, t, v * one])
    g = np.select([i == 0, i == 1, i == 2, i == 3, i == 4, i == 5],
                  [t, v * one, v * one, q, p, p])
    b = np.select([i == 0, i == 1, i == 2, i == 3, i == 4, i == 5],
                  [p, p, t, v * one, v * one, q])
    return np.stack([r, g, b], axis=-1).astype(np.float32)


def hsv_scalar(h, s, v):
    """Scalar HSV -> np.float32 RGB(3)."""
    return hsv2rgb(np.array([h], np.float32), s, v)[0]


def plane_array(frame, p):
    """Writable numpy view of VapourSynth plane p (uint8), R81 API."""
    sw, sh = frame.format.subsampling_w, frame.format.subsampling_h
    pw, ph = frame.width >> sw, frame.height >> sh
    stride = frame.get_stride(p)
    ptr = frame.get_write_ptr(p).value
    buf = (ctypes.c_uint8 * (stride * ph)).from_address(ptr)
    return np.frombuffer(buf, dtype=np.uint8).reshape(ph, stride)[:, :pw]


# ---------------------------------------------------------------------------
# Audio analysis (done once)
# ---------------------------------------------------------------------------
def analyse(path):
    with wave.open(path, "rb") as wf:
        sr, nch, nframes = wf.getframerate(), wf.getnchannels(), wf.getnframes()
        raw = wf.readframes(nframes)
    data = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    data = data.reshape(-1, nch)
    mono = data.mean(axis=1)
    stereo = data[:, 0] if nch == 1 else data

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
    hi_idx = np.where(freqs > 6000.0)[0]

    spec_db = np.zeros((n_frames, NBARS), np.float32)
    bass_db = np.zeros(n_frames, np.float32)
    hi_db = np.zeros(n_frames, np.float32)

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
        hi_db[i] = 20.0 * np.log10(mag[hi_idx].mean())

    def norm(db, lo_pc, hi_pc):
        lo, hi = np.percentile(db, lo_pc), np.percentile(db, hi_pc)
        return np.clip((db - lo) / (hi - lo + 1e-6), 0.0, 1.0)

    # per-band levels, normalised and temporally smoothed (fast attack/slow release)
    level = norm(spec_db, 25, 99.7) ** 1.25
    smooth = np.zeros_like(level)
    prev = np.zeros(NBARS, np.float32)
    for i in range(n_frames):
        prev = np.where(level[i] > prev,
                        prev + (level[i] - prev) * 0.55,
                        prev * 0.80)
        smooth[i] = prev

    # peak-hold caps with slow fall
    caps = np.zeros_like(smooth)
    cap = np.zeros(NBARS, np.float32)
    for i in range(n_frames):
        cap = np.maximum(smooth[i], cap - 0.028)
        caps[i] = cap

    bass = norm(bass_db, 10, 99)
    hi = norm(hi_db, 40, 99)

    # kick envelope: fast attack, ~0.3s release, plus a strobe flag
    kick = np.zeros(n_frames, np.float32)
    k = 0.0
    for i in range(n_frames):
        k = max(bass[i], k * (1.0 - 1.0 / (FPS * 0.25)))
        kick[i] = k

    # oscilloscope trace: 2048-sample window per frame, resampled to W points
    xs = np.arange(W)
    trace = np.zeros((n_frames, W), np.float32)
    for i in range(n_frames):
        c = i * hop + hop // 2
        seg = mono[c - 1024:c + 1024]
        if seg.shape[0] < 2048:
            seg = np.pad(seg, (0, 2048 - seg.shape[0]))
        trace[i] = np.interp(np.linspace(0, 2047, W), np.arange(2048), seg)
    peak = np.percentile(np.abs(trace), 99.5) + 1e-6
    trace = np.clip(trace / peak, -1.0, 1.0)

    return dict(sr=sr, duration=duration, n_frames=n_frames, level=smooth,
                caps=caps, bass=bass, hi=hi, kick=kick, trace=trace)


A = analyse(AUDIO_PATH)
NF = A["n_frames"]

# ---------------------------------------------------------------------------
# Static layers (built once)
# ---------------------------------------------------------------------------
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
rr = np.sqrt((xx - CENTRE[0]) ** 2 + (yy - CENTRE[1]) ** 2)

# concrete: static fine noise, low amplitude
_concrete = np.random.default_rng(7).random((H, W)).astype(np.float32)
concrete = (_concrete - 0.5) * 0.05

# vignette + subtle top-down falloff
vx = (xx - W / 2) / (W / 2)
vy = (yy - H / 2) / (H / 2)
vignette = np.clip(1.0 - 0.55 * (vx ** 2 + vy ** 2), 0.35, 1.0).astype(np.float32)

# scanlines + rolling film-grain tile
scanline = (1.0 - 0.16 * (yy % 2)).astype(np.float32)
grain_tile = np.random.default_rng(99).standard_normal((H, W)).astype(np.float32)

# spectrum bar geometry
BW = W // NBARS
bar_x0 = (np.arange(NBARS) * BW + 1).astype(np.int32)
bar_x1 = (np.arange(NBARS) * BW + BW - 2).astype(np.int32)
BAR_MAXH = int(H * 0.42)

# floor grid geometry
VLINES = 23
vline_xb = (CENTRE[0] + (np.arange(VLINES) - (VLINES - 1) / 2)
            * (W * 0.105)).astype(np.float32)
floor_rows = np.arange(HORIZON_Y, H)
floor_depth = ((floor_rows - HORIZON_Y) / (H - HORIZON_Y)).astype(np.float32)

GREEN, BLUE, RED = 0, 1, 2   # planar RGB24 plane order


def compose(n):
    """Build one RGB frame (float 0..1) for frame index n."""
    i = min(n, NF - 1)
    t = n / FPS
    kick = float(A["kick"][i])
    bars = A["level"][i]
    caps = A["caps"][i]
    hi = float(A["hi"][i])
    bass = float(A["bass"][i])
    hue0 = (0.60 + 0.06 * math.sin(t * 0.6)) % 1.0

    img = np.empty((H, W, 3), np.float32)
    img[:] = BG
    img += concrete[..., None] * 0.6
    # horizon glow that breathes with the kick
    glow = np.exp(-((yy - HORIZON_Y) / (H * 0.16)) ** 2)[..., None]
    img += glow * hsv_scalar((hue0 + 0.5) % 1.0, 0.9, 0.10 * (0.4 + kick))

    # ---- hypnotic concentric rings (bass-reactive, slow rotation) ----
    ring_shift = bass * 26.0 + 6.0 * math.sin(t * 0.7)
    spacing = 46.0
    phase = np.mod(rr - ring_shift, spacing) - spacing / 2.0
    ringw = 3.0 + 2.0 * bass
    rings = np.exp(-(phase / ringw) ** 2).astype(np.float32)
    rc = hsv_scalar(hue0, 0.75, 0.85)
    img += rings[..., None] * rc * (0.10 + 0.35 * bass + 0.15 * kick)

    # ---- receding perspective floor ----
    grid_col = np.array([0.10, 0.13, 0.20], np.float32)
    scroll = (t * 0.35) % 1.0
    for j in range(10):
        frac = (scroll + j * 0.11) % 1.0
        row = int(HORIZON_Y + (H - HORIZON_Y) * (frac ** 2))
        if 0 <= row < H:
            img[row:row + 1, :, :] += grid_col * (1.0 - frac) * (0.5 + 0.8 * kick)
    for xb in vline_xb:
        xs = (CENTRE[0] + (xb - CENTRE[0]) * floor_depth).astype(np.int32)
        xs = np.clip(xs, 0, W - 1)
        img[floor_rows, xs, :] += grid_col * 0.35 * (0.5 + 0.5 * kick)

    # ---- sweeping light beam (talks to the hi-hats) ----
    xb = (t * 90.0) % (W * 1.4) - W * 0.2
    beam = np.exp(-((xx - xb) / (W * 0.05)) ** 2).astype(np.float32)
    img += beam[..., None] * hsv_scalar((hue0 + 0.45) % 1.0, 0.6, 0.6) * (0.05 + 0.5 * hi)

    # ---- neon spectrum tubes + reflections + peak caps ----
    xs_all = np.arange(W)
    for b in range(NBARS):
        x0, x1 = int(bar_x0[b]), int(bar_x1[b])
        hgt = int(bars[b] * BAR_MAXH)
        if hgt < 1:
            hgt = 1
        hue = (hue0 + 0.30 * b / NBARS) % 1.0
        col = hsv_scalar(hue, 0.85, 1.0)
        y0 = HORIZON_Y - hgt
        # bloom halo
        img[max(0, y0 - 10):HORIZON_Y, max(0, x0 - 5):x1 + 5, :] += col * 0.10
        # tube body
        img[y0:HORIZON_Y, x0:x1, :] += col * 0.95
        # bright core edge
        img[y0:HORIZON_Y, x0:x0 + 1, :] += col * 0.5
        # wet-floor reflection (dim, mirrored)
        rh = min(hgt, int((H - HORIZON_Y) * 0.9))
        img[HORIZON_Y:HORIZON_Y + rh, x0:x1, :] += col[None, None, :] * 0.22
        # peak-hold cap
        cy = int(HORIZON_Y - caps[b] * BAR_MAXH)
        img[max(0, cy - 2):cy + 2, x0:x1, :] += hsv_scalar((hue + 0.08) % 1.0, 0.55, 1.0) * 1.2

    # ---- oscilloscope trace ----
    tr = A["trace"][i]
    y0s = H * 0.52
    amp = H * 0.11
    ys = np.clip((y0s - tr * amp).astype(np.int32), 1, H - 2)
    scope_col = hsv_scalar((hue0 + 0.15) % 1.0, 0.7, 1.0)
    for off, a in ((0, 1.0), (-1, 0.45), (1, 0.45), (-2, 0.18), (2, 0.18)):
        img[np.clip(ys + off, 0, H - 1), xs_all, :] += scope_col * a * 0.9

    # ---- kick strobe + chromatic glitch + grain ----
    if kick > 0.05:
        strobe = hsv_scalar((hue0 + 0.55) % 1.0, 0.16, 1.0)
        img += (kick ** 1.8) * strobe * 0.45
    if kick > 0.55:
        g = int((kick - 0.55) * 22.0)
        if g > 0:
            img[:, :, RED] = np.roll(img[:, :, RED], g, axis=1)
            img[:, :, BLUE] = np.roll(img[:, :, BLUE], -g, axis=1)
    g_amt = 0.020 + 0.05 * kick
    grain = np.roll(grain_tile, (n * 7) % H, axis=0)
    grain = np.roll(grain, (n * 13) % W, axis=1)
    img += grain[..., None] * g_amt

    # ---- post: scanlines + vignette ----
    img *= scanline[..., None]
    img *= vignette[..., None]
    return img


def draw(n, f):
    """std.ModifyFrame callback: render frame n into the RGB24 planes."""
    img = compose(n)
    np.clip(img, 0.0, 1.0, out=img)
    out = (img * 255.0 + 0.5).astype(np.uint8)
    fc = f.copy()
    plane_array(fc, GREEN)[:] = out[:, :, 0]
    plane_array(fc, BLUE)[:] = out[:, :, 1]
    plane_array(fc, RED)[:] = out[:, :, 2]
    return fc


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------
blank = core.std.BlankClip(width=W, height=H, format=vs.RGB24,
                           length=NF, fpsnum=FPS, fpsden=1)
rgb = core.std.ModifyFrame(blank, blank, draw)
clip = core.resize.Bicubic(rgb, format=vs.YUV420P8, matrix_s="470bg",
                           range_s="limited")
clip.set_output()
