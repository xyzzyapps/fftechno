"""visualizer.vpy - VapourSynth audio-reactive visualizer for output/techno.wav.

Aesthetic: a film-leader / "countdown" ident (Academy-leader style) crossed with
dark Berlin techno - heavy grain, a rotating sweep hand and crosshair, a large
segmented numeral counting down one per bar, scratch flicker, and the spectrum as
amber audio-reactive bars along the bottom.

Run (video only, piped to ffmpeg):
    .venv\\Scripts\\vspipe.exe -c y4m visualizer.vpy - | ffmpeg -f yuv4mpegpipe -i - ...
Or inspect:  .venv\\Scripts\\vspipe.exe -i visualizer.vpy -

Design notes
------------
- Audio analysis happens once at script load (numpy STFT -> per-frame band
  levels). Frames are drawn in pure numpy inside a std.ModifyFrame callback so the
  whole visual is deterministic and reproducible.
- VapourSynth R81 frame planes are read-only memoryviews; writing uses
  frame.copy() + get_write_ptr(plane).value + get_stride(plane) with ctypes.
- Authored as planar RGB24 (planes = G, B, R) and converted to YUV420P8 by the
  built-in resize for y4m piping.
- Numerals are drawn as 7-segment shapes in numpy (no external font files).
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
CENTRE = (W * 0.5, H * 0.44)
SWEEP_R = 330.0                     # radius of the swept arc
BAR = 60.0 / 140.0 * 4.0            # bar length in seconds (1.7142857)
BAR_MAXH = int(H * 0.22)
BG = np.array([0.030, 0.033, 0.041], np.float32)     # cold film black
STEEL = np.array([0.55, 0.58, 0.66], np.float32)     # sweep / crosshair tint
AMBER = np.array([1.00, 0.72, 0.16], np.float32)     # numeral


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


# 7-segment digit definitions ------------------------------------------------
SEG = {
    0: "abcdef", 1: "bc", 2: "abged", 3: "abgcd", 4: "fgbc",
    5: "afgcd", 6: "afgecd", 7: "abc", 8: "abcdefg", 9: "abcdfg",
}


def draw_digit(img, d, cx, cy, w, h, th, colour):
    """Additively draw 7-segment numeral d centred at (cx,cy) into float RGB img."""
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
        for pad, alpha in ((0, 1.0), (7, 0.35), (16, 0.14)):
            img[max(0, y0 - pad):min(H, y1 + pad),
                max(0, x0 - pad):min(W, x1 + pad), :] += colour * alpha
    return img


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

    return dict(sr=sr, duration=duration, n_frames=n_frames, level=smooth, kick=kick)


A = analyse(AUDIO_PATH)
NF = A["n_frames"]

# ---------------------------------------------------------------------------
# Static layers (built once)
# ---------------------------------------------------------------------------
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
rr = np.sqrt((xx - CENTRE[0]) ** 2 + (yy - CENTRE[1]) ** 2)
phi = np.mod(np.arctan2(yy - CENTRE[1], xx - CENTRE[0]), 2 * np.pi).astype(np.float32)

vx = (xx - W / 2) / (W / 2)
vy = (yy - H / 2) / (H / 2)
vignette = np.clip(1.0 - 0.55 * (vx ** 2 + vy ** 2), 0.35, 1.0).astype(np.float32)
scanline = (1.0 - 0.14 * (yy % 2)).astype(np.float32)
grain_tile = np.random.default_rng(99).standard_normal((H, W)).astype(np.float32)
scratch_x = np.random.default_rng(5).integers(0, W, size=64)

BW = W // NBARS
bar_x0 = (np.arange(NBARS) * BW + 2).astype(np.int32)
bar_x1 = (np.arange(NBARS) * BW + BW - 3).astype(np.int32)

GREEN, BLUE, RED = 0, 1, 2   # planar RGB24 plane order


def compose(n):
    """Build one RGB frame (float 0..1) for frame index n."""
    i = min(n, NF - 1)
    t = n / FPS
    kick = float(A["kick"][i])
    bars = A["level"][i]

    img = np.empty((H, W, 3), np.float32)
    img[:] = BG

    # ---- rotating sweep (one revolution per bar) ----
    theta = 2.0 * np.pi * ((t % BAR) / BAR)
    trail = np.mod(theta - phi, 2 * np.pi) < 0.55
    img += trail[..., None] * STEEL * 0.045
    edge = np.exp(-(np.mod(theta - phi, 2 * np.pi) / 0.022) ** 2).astype(np.float32)
    img += edge[..., None] * STEEL * 0.55
    ring = np.exp(-((rr - SWEEP_R) / 2.2) ** 2).astype(np.float32)
    img += (ring * (phi < theta))[..., None] * np.array([0.75, 0.70, 0.55], np.float32) * 0.55

    # ---- crosshair ----
    img[:, W // 2 - 1:W // 2 + 2, :] += STEEL * 0.14
    img[H // 2 - 1:H // 2 + 2, :, :] += STEEL * 0.14

    # ---- countdown numeral (8,7,6..1, one per bar) ----
    number = max(1, min(8, 8 - int(t / BAR)))
    flick = 0.9 + 0.1 * math.sin(t * 37.0)
    draw_digit(img, number, CENTRE[0], CENTRE[1] - 40, 230, 400, 40,
               AMBER * flick)

    # ---- spectrum: amber bars rising off the bottom ----
    for b in range(NBARS):
        hgt = int(bars[b] * BAR_MAXH)
        if hgt < 1:
            hgt = 1
        hue = (0.10 - 0.06 * b / NBARS) % 1.0      # amber -> red
        col = hsv_scalar(hue, 0.85, 1.0)
        x0, x1 = int(bar_x0[b]), int(bar_x1[b])
        y0 = H - hgt
        img[max(0, y0 - 8):H, max(0, x0 - 4):x1 + 4, :] += col * 0.10
        img[y0:H, x0:x1, :] += col * 0.95
    img[H - 2:H, :, :] += AMBER * 0.25               # baseline

    # ---- film grain + flicker ----
    grain = np.roll(grain_tile, (n * 7) % H, axis=0)
    grain = np.roll(grain, (n * 13) % W, axis=1)
    img += grain[..., None] * (0.055 + 0.06 * kick)
    img *= (0.92 + 0.08 * ((n * 2654435761) % 997) / 997.0)

    # ---- vertical scratches (occasional) ----
    if n % 23 < 2:
        for s in range(2):
            xs = int(scratch_x[(n + s * 7) % 64])
            img[:, xs:xs + 1, :] += STEEL * 0.5 * (0.5 + 0.5 * kick)

    # ---- kick strobe + jitter ----
    if kick > 0.05:
        img += (kick ** 1.8) * np.array([0.5, 0.5, 0.47], np.float32) * 0.45
    if kick > 0.6:
        j = int((kick - 0.6) * 14.0)
        if j > 0:
            img = np.roll(img, j, axis=0)

    # ---- grade: scanlines, vignette, cool steel tint ----
    img *= scanline[..., None]
    img *= vignette[..., None]
    img *= np.array([0.94, 0.97, 1.05], np.float32)
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
