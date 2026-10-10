"""visualizer.vpy - VapourSynth + GLSL (vs-placebo) visualizer for output/techno.wav.

Aesthetic: black-and-white. Images from the `ascii/` folder are converted to
ASCII art (a self-contained numpy bitmap font, no external deps), looped at
random one every 2 bars, and a Berlin-techno overlay (hypnotic rings, audio
spokes, grid, scanlines, kick glitch, grain) is drawn over them in monochrome by
a GPU GLSL shader.

Pipeline
--------
1. At load: decode each needed image with ffmpeg -> 120x72 gray grid -> ASCII
   bitmap -> cached uint8 frame. Random image per 2-bar block (deterministic RNG).
2. Per frame: write the ASCII frame into the luma plane and the audio data strip
   (64 bands + bass + kick + energy) into rows 0-3 of a YUV444P16 clip.
3. core.placebo.Shader runs a GLSL shader that reads the ASCII (HOOKED_tex), the
   strip (audio reactivity) and `frame` (time) and draws the B/W overlay.
4. Convert to YUV420P8 for y4m piping.

Run:  .venv\\Scripts\\vspipe.exe -c y4m visualizer.vpy - | ffmpeg -f yuv4mpegpipe -i - ...
Info: .venv\\Scripts\\vspipe.exe -i visualizer.vpy -
"""

import ctypes
import glob
import math
import subprocess
import wave

import numpy as np
import vapoursynth as vs

core = vs.core

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
AUDIO_PATH = "output/techno.wav"
IMG_DIR = "ascii"
W, H, FPS = 1920, 1080, 30
NBARS = 64
BAR = 60.0 / 140.0 * 4.0            # 1.7142857 s
CELL = 24                           # strip pixels per value
STRIP_ROWS = 4
IMG_PERIOD = 60.0 / 140.0           # seconds per ascii image (one per beat = rapid)

GRID_W, GRID_H = 80, 45             # ascii cells
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
//!DESC ascii bw berlin

#define FPS 30.0

float strip(float idx){ return HOOKED_tex(vec2((idx*24.0+12.0)/1920.0, 1.5/1080.0)).x; }
float band(float b){ return strip(b); }
float aux(float i){ return strip(64.0+i); }
float hash(float n){ return fract(sin(n)*43758.5453); }

vec4 hook(){
    float t = float(frame)/FPS;
    float bass = aux(0.0), kick = aux(1.0), energy = aux(2.0);
    vec2 res = target_size;
    vec2 uv = (HOOKED_pos*res - 0.5*res)/res.y;
    float r = length(uv);
    float ang = atan(uv.y, uv.x) + t*0.10;
    float seg = 8.0;
    float ka = abs(mod(ang, 6.28318/seg) - 3.14159/seg);

    float lum = HOOKED_tex(HOOKED_pos).x;                     // ascii base

    float rings = smoothstep(0.86, 1.0, sin(1.0/(r+0.12)*3.0 - t*3.0 + bass*6.0));
    float spokes = 0.0;
    for(int i=0;i<8;i++){
        spokes += band(float(i)*8.0) * exp(-22.0*abs(ka - 0.12*float(i)));
    }
    float grid = smoothstep(0.90, 1.0, abs(fract(uv.x*12.0 + t*0.15)-0.5)*2.0);

    float col = lum*0.95 + rings*0.5 + spokes*0.45 + grid*0.18;
    col += exp(-9.0*r) * (0.15 + kick*0.9);
    col *= 1.0 - 0.6*r;
    col *= 0.88 + 0.12*sin(HOOKED_pos.y*res.y*1.5708);
    col += (random - 0.5)*0.06;
    if(step(0.78, kick) > 0.5){
        col = col*1.5 + (hash(floor(t*30.0)) - 0.5)*0.3;
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
    out = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path,
         "-vf", f"scale={GRID_W}:{GRID_H}:flags=area,format=gray",
         "-f", "rawvideo", "-"],
        capture_output=True)
    return np.frombuffer(out.stdout, np.uint8)[:GRID_W * GRID_H].reshape(GRID_H, GRID_W)


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
TOTAL_BARS = int(math.ceil(A["duration"] / BAR))

# ---------------------------------------------------------------------------
# ASCII frames: one random image per beat (rapid), rendered on demand + cached
# ---------------------------------------------------------------------------
_files = sorted(glob.glob(f"{IMG_DIR}/*.jpg")) + sorted(glob.glob(f"{IMG_DIR}/*.png"))
_grids = [decode_gray(p) for p in _files] if _files else []
N_IMG_BLOCKS = int(math.ceil(A["duration"] / IMG_PERIOD)) + 1
_rng = np.random.default_rng(20261010)
_picks = _rng.integers(0, max(1, len(_files)), size=N_IMG_BLOCKS)
_render_cache = {}


def ascii_for_block(blk):
    """Render (and cache) the ASCII frame for a block; bounded cache."""
    if blk not in _render_cache:
        if len(_render_cache) > 8:
            _render_cache.clear()
        if _grids:
            _render_cache[blk] = render_ascii(_grids[int(_picks[blk])])
        else:
            _render_cache[blk] = np.zeros((H, W), np.uint8)
    return _render_cache[blk]


def build_data(n, f):
    fc = f.copy()
    luma = plane_u16(fc, 0)
    i = min(n, NF - 1)
    blk = min(int((n / FPS) / IMG_PERIOD), N_IMG_BLOCKS - 1)
    luma[:] = ascii_for_block(blk).astype(np.uint16) * 257
    vals = np.concatenate([A["level"][i], [A["bass"][i], A["kick"][i],
                                          A["energy"][i]]]).astype(np.float32)
    for k, v in enumerate(vals):
        x0 = k * CELL
        luma[0:STRIP_ROWS, x0:x0 + CELL] = np.uint16(np.clip(v, 0, 1) * 65535)
    return fc


blank = core.std.BlankClip(width=W, height=H, format=vs.YUV444P16,
                           length=NF, fpsnum=FPS, fpsden=1)
data = core.std.ModifyFrame(blank, blank, build_data)

shaded = core.placebo.Shader(data, shader_s=SHADER, width=W, height=H,
                             sigmoidize=False, linearize=False, matrix=5)

clip = core.resize.Bicubic(shaded, format=vs.YUV420P8, matrix_in_s="470bg",
                           matrix_s="470bg", range_in_s="limited",
                           range_s="limited")
clip.set_output()
