"""visualizer.vpy - VapourSynth + GLSL dancing-girl visualizer.

The main visual is a black-and-white, edge-detected dancing girl: `fftechno
girl` mattes the source clip (RVM), composites her over black and edge-detects
the result, producing a compact frame stack (``output/girl_frames.npy``) whose
length is a whole number of beats. This script loops that stack across the whole
track (``output/techno.wav``) and a GPU GLSL shader (vs-placebo) adds a subtle
monochrome Berlin overlay (hypnotic rings, audio spokes, grid, grain) plus a
kick-synced brightness punch.

If ``girl_frames.npy`` is missing it falls back to the original ASCII art of the
images in ``ascii/``.

Pipeline
--------
1. Analyse the mastered WAV (64 bands + bass + kick + energy).
2. Per frame: write the edge-detected girl frame into the luma plane and the
   audio data strip into the top rows of a low-res YUV444P16 clip.
3. Upscale to 1920x1080; ``core.placebo.Shader`` reads the girl (``HOOKED_tex``),
   the strip (audio reactivity) and ``frame`` (time) and draws the B/W overlay.
4. Convert to YUV420P8 for y4m piping.

Run:  .venv\\Scripts\\vspipe.exe -c y4m visualizer.vpy - | ffmpeg -f yuv4mpegpipe -i - ...
Info: .venv\\Scripts\\vspipe.exe -i visualizer.vpy -
"""

import ctypes
import glob
import math
import os
import subprocess
import wave

import numpy as np
import vapoursynth as vs

core = vs.core

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
AUDIO_PATH = os.environ.get("FFTECHNO_AUDIO", "output/techno.wav")
GIRL_FRAMES = os.environ.get("FFTECHNO_GIRL_FRAMES", "output/girl_frames.npy")
# "reset" | "trail" | "build" for the Pollock look (empty = edge, no accumulation).
POLLOCK = os.environ.get("FFTECHNO_POLLOCK", "").strip()
IMG_DIR = "ascii"
# When set (vspipe sees FFTECHNO_STATIC=1) the output is a single frozen frame
# repeated for the whole duration -> no animation.
STATIC = os.environ.get("FFTECHNO_STATIC") == "1"
W, H, FPS = 1920, 1080, 30
GW, GH = 960, 540                    # low-res clip the girl frames are drawn into

NBARS = 64
CELL = GW // NBARS                   # strip pixels per value (960/64 = 15)
STRIP_ROWS = 4

GRID_W, GRID_H = 80, 45             # ascii fallback cells
CELL_W, CELL_H = W // GRID_W, H // GRID_H
RAMP = " .:-=+*#%@"

GLYPHS = {
    ".": ["00000", "00000", "00000", "00000", "00000", "00100", "00100"],
    ":": ["00000", "00100", "00100", "00000", "00100", "00100", "00000"],
    "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    "=": ["00000", "00000", "11111", "00000", "11111", "00000", "00000"],
    "+": ["00000", "00100", "00100", "11111", "00100", "00100", "00000"],
    "*": ["00100", "10101", "01110", "11111", "01110", "10101", "00100"],
    "#": ["01010", "01010", "11111", "01010", "11111", "01010", "01010"],
    "%": ["11001", "11010", "00010", "00100", "01000", "01011", "10011"],
    "@": ["01110", "10001", "10111", "10101", "10111", "10000", "01110"],
}
_GLYPH_ARR = {k: np.array([[int(c) for c in row] for row in v], np.uint8)
              for k, v in GLYPHS.items()}


# ---------------------------------------------------------------------------
# GLSL shader (mpv/libplacebo syntax; `frame` + `random` provided by vs-placebo)
# ---------------------------------------------------------------------------
SHADER = """
//!HOOK MAIN
//!BIND HOOKED
//!DESC girl bw berlin

#define FPS 30.0

// The audio data strip lives in the top rows of HOOKED (64 values across the
// width); sample it in normalised coordinates.
float strip(float idx){ return HOOKED_tex(vec2((idx+0.5)/64.0, 2.0/1080.0)).x; }
float band(float b){ return strip(b); }
float aux(float i){ return strip(64.0+i); }
float hash(float n){ return fract(sin(n)*43758.5453); }

vec4 hook(){
    // The top rows of HOOKED hold the audio data strip, not picture - hide it.
    if (HOOKED_pos.y < 9.0/1080.0) return vec4(0.0, 0.0, 0.0, 1.0);
    float t = float(frame)/FPS;
    float bass = aux(0.0), kick = aux(1.0), energy = aux(2.0);
    vec2 res = target_size;
    vec2 uv = (HOOKED_pos*res - 0.5*res)/res.y;
    float r = length(uv);
    float ang = atan(uv.y, uv.x) + t*0.10;
    float seg = 8.0;
    float ka = abs(mod(ang, 6.28318/seg) - 3.14159/seg);

    float lum = HOOKED_tex(HOOKED_pos).x;                     // girl edges

    float rings = smoothstep(0.86, 1.0, sin(1.0/(r+0.12)*3.0 - t*3.0 + bass*6.0));
    float spokes = 0.0;
    for(int i=0;i<8;i++){
        spokes += band(float(i)*8.0) * exp(-22.0*abs(ka - 0.12*float(i)));
    }
    float grid = smoothstep(0.90, 1.0, abs(fract(uv.x*12.0 + t*0.15)-0.5)*2.0);

    float col = lum*1.05;
    col += lum*kick*0.9;                                      // edges flash on kick
    col += rings*0.16 + spokes*0.14 + grid*0.05;
    col += exp(-9.0*r) * (0.05 + kick*0.18);
    col *= 1.0 - 0.42*r;                                      // vignette
    col *= 0.92 + 0.08*sin(HOOKED_pos.y*res.y*1.5708);        // scanline
    col += (random - 0.5)*0.03;                               // film grain
    if(step(0.78, kick) > 0.5){
        col = col*1.35 + (hash(floor(t*30.0)) - 0.5)*0.15;    // kick glitch
    }
    return vec4(vec3(col), 1.0);
}
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def plane_u16(frame, p):
    """Writable numpy uint16 view of a 16-bit plane (R81 API)."""
    sw, sh = frame.format.subsampling_w, frame.format.subsampling_h
    pw, ph = frame.width >> sw, frame.height >> sh
    stride = frame.get_stride(p)
    ptr = frame.get_write_ptr(p).value
    buf = (ctypes.c_uint8 * (stride * ph)).from_address(ptr)
    return np.frombuffer(buf, dtype=np.uint16).reshape(ph, stride // 2)[:, :pw]


def decode_gray(path):
    """Decode an image to a GRID_H x GRID_W uint8 grayscale grid via ffmpeg."""
    try:
        out = subprocess.run(
            ["ffmpeg", "-nostdin", "-v", "error", "-i", path,
             "-vf", f"scale={GRID_W}:{GRID_H}:flags=area,format=gray",
             "-f", "rawvideo", "-"],
            capture_output=True, timeout=30)
        buf = np.frombuffer(out.stdout, np.uint8)
        if buf.size < GRID_W * GRID_H:
            return np.zeros((GRID_H, GRID_W), np.uint8)
        return buf[:GRID_W * GRID_H].reshape(GRID_H, GRID_W).astype(np.uint8)
    except Exception:
        return np.zeros((GRID_H, GRID_W), np.uint8)


def render_ascii(grid):
    """Map a grayscale grid to an ASCII-art uint8 frame (H x W)."""
    canvas = np.zeros((H, W), np.uint8)
    idx = ((grid.astype(np.float32) / 255.0) * (len(RAMP) - 1)).round().astype(np.int32)
    for cy in range(GRID_H):
        for cx in range(GRID_W):
            g = _GLYPH_ARR.get(RAMP[idx[cy, cx]])
            if g is None:
                continue
            tile = np.repeat(np.repeat(g, 3, 0), 4, 1) * 255   # 21 x 20
            y0, x0 = cy * CELL_H, cx * CELL_W
            reg = canvas[y0:y0 + tile.shape[0], x0:x0 + tile.shape[1]]
            np.maximum(reg, tile, out=reg)
    return canvas


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
        prev = np.where(level[i] > prev, prev + (level[i] - prev) * 0.55, prev * 0.80)
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

# ---------------------------------------------------------------------------
# Main visual: the edge-detected dancing girl, looped on the beat grid
# ---------------------------------------------------------------------------
if os.path.exists(GIRL_FRAMES):
    GIRL = np.load(GIRL_FRAMES, mmap_mode="r")      # (N, GH, GW) uint8
    GIRL_N = GIRL.shape[0]
else:
    GIRL = None
    GIRL_N = 0

# ---------------------------------------------------------------------------
# Fallback: ASCII art of the images in ascii/ (only if there is no girl stack)
# ---------------------------------------------------------------------------
_fallback_needed = GIRL is None
if _fallback_needed:
    _files = sorted(glob.glob(f"{IMG_DIR}/*.jpg")) + sorted(glob.glob(f"{IMG_DIR}/*.png"))
    _grids = [decode_gray(p) for p in _files] if _files else []
    N_IMGS = len(_files)
    IMG_PERIOD = 3.0
    if N_IMGS:
        IMG_PERIOD = A["duration"] / (3 * N_IMGS)
    N_IMG_BLOCKS = int(math.ceil(A["duration"] / IMG_PERIOD)) + 1
    _rng = np.random.default_rng(20261010)
    if N_IMGS:
        _playlist = list(range(N_IMGS)) * 3
        _rng.shuffle(_playlist)
        while len(_playlist) < N_IMG_BLOCKS:
            _playlist.append(int(_rng.integers(0, N_IMGS)))
        _picks = np.array(_playlist[:N_IMG_BLOCKS], dtype=int)
    else:
        _picks = np.zeros(N_IMG_BLOCKS, dtype=int)
    _render_cache = {}

    def ascii_for_block(blk):
        if blk not in _render_cache:
            if len(_render_cache) > 8:
                _render_cache.clear()
            _render_cache[blk] = (render_ascii(_grids[int(_picks[blk])])
                                  if _grids else np.zeros((H, W), np.uint8))
        return _render_cache[blk]

_FILL = NF // 2                     # representative frame used when STATIC
_blank = np.zeros((GH, GW), np.uint8)

# Running paint canvas for the Pollock look (accumulated frame to frame).
_CANVAS = np.zeros((GH, GW), np.float32)
_DECAY = {"reset": 0.90, "trail": 0.85, "build": 0.995}.get(POLLOCK, 1.0)
_RNG = np.random.default_rng(7)
_SPLATTER = 0.015                            # fresh paint flecks per frame


def build_data(n, f):
    fc = f.copy()
    luma = plane_u16(fc, 0)
    i = _FILL if STATIC else min(n, NF - 1)
    if GIRL is not None:
        stroke = np.asarray(GIRL[i % GIRL_N], np.float32)
        if STATIC or not POLLOCK:
            canvas = stroke
        else:
            if POLLOCK == "reset" and (i % GIRL_N) == 0:
                _CANVAS[:] = 0.0
            np.multiply(_CANVAS, _DECAY, out=_CANVAS)
            np.maximum(_CANVAS, stroke, out=_CANVAS)
            canvas = _CANVAS
        if POLLOCK and not STATIC:
            speckle = (_RNG.random((GH, GW)) < _SPLATTER).astype(np.float32) * 255.0
            canvas = np.maximum(canvas, speckle)
        luma[:] = np.clip(canvas, 0, 255).astype(np.uint16) * 257
    else:
        blk = min(int((i / FPS) / IMG_PERIOD), N_IMG_BLOCKS - 1)
        small = render_ascii(_grids[int(_picks[blk])]) if _grids else _blank
        # downscale the ascii canvas (H x W) to the low-res clip with nearest
        # sampling so the fallback still works.
        ys = (np.arange(GH) * (H // GH)).astype(int)
        xs = (np.arange(GW) * (W // GW)).astype(int)
        luma[:] = small[np.ix_(ys, xs)].astype(np.uint16) * 257
    vals = np.concatenate([A["level"][i], [A["bass"][i], A["kick"][i],
                                          A["energy"][i]]]).astype(np.float32)
    for k, v in enumerate(vals):
        x0 = k * CELL
        luma[0:STRIP_ROWS, x0:x0 + CELL] = np.uint16(np.clip(v, 0, 1) * 65535)
    return fc


blank = core.std.BlankClip(width=GW, height=GH, format=vs.YUV444P16,
                           length=(1 if STATIC else NF), fpsnum=FPS, fpsden=1)
data = core.std.ModifyFrame(blank, blank, build_data)
big = core.resize.Bicubic(data, width=W, height=H)

shaded = core.placebo.Shader(big, shader_s=SHADER, width=W, height=H,
                             sigmoidize=False, linearize=False, matrix=5)

clip = core.resize.Bicubic(shaded, format=vs.YUV420P8, matrix_in_s="470bg",
                           matrix_s="470bg", range_in_s="limited",
                           range_s="limited")
if STATIC:
    clip = core.std.Loop(clip, NF)      # hold the single frame for the full length
clip.set_output()
