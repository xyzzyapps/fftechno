"""Dancing-girl visual: turn the ``ascii/`` clip into a black-and-white loop or
still-sequence for the video.

Looks
-----
``pollock`` (default)
    **Whole frame** (no matte): ``edgedetect`` thin lines, crossed rotated copies,
    stacked into a running paint canvas - an all-over abstract "painting".
``edge``
    RVM-matte the girl, keep only her (drops the crowd), ``edgedetect`` a clean
    white line drawing on black.
``outline``
    RVM-matte the girl, keep only her (drops the crowd) and draw **only her
    silhouette outline** (no face/interior detail). The **blue hair is preserved
    by chroma-keying** the original colour. Random stills are cut in **on the
    beat** (BPM read from ``song.md``), so the picture strobes in time.

Pipeline
--------
1. Decode ``GIRL_CROP_START .. +GIRL_CROP_DURATION`` (2.0 s..5.0 s) at native
   size/fps.
2. Per look: matte (edge/outline) or use as-is (pollock).
3. ffmpeg / numpy: fit to 16:9 with black bars, then the look.
4. Write the frame data + a standalone ``output/girl_loop.mp4``.

For ``outline`` the "frame data" is a set of per-source-frame sprites plus a
per-output-frame index array (the beat-synced random picks), consumed by
``visualizer.vpy``.
"""

from __future__ import annotations

import glob
import re
import subprocess
from pathlib import Path

import numpy as np

from . import config as C
from .proc import ffmpeg

# ---------------------------------------------------------------------------
# Look definitions
# ---------------------------------------------------------------------------
_EDGE = "edgedetect=low=0.08:high=0.25"          # clean white line drawing


def _fit(out_w: int, out_h: int) -> str:
    """Resample to the video fps and fit a 16:9 frame with black bars."""
    return (f"fps={C.VIDEO_FPS},scale=-2:{out_h}:flags=lanczos,"
            f"pad={out_w}:{out_h}:(ow-iw)/2:(oh-ih)/2:black")


def _pollock_filter(out_w: int, out_h: int, accumulate: bool) -> str:
    """Filtergraph: whole-frame edges -> crossed gestures (+ splatter if accumulated).

    The stroke layer (edges + rotated copies) is meant to be accumulated over
    time by the visualizer; only the standalone loop uses ``accumulate=True``
    (``tblend`` build-up) with a fresh splatter overlay.
    """
    head = (
        f"[0:v]{_fit(out_w, out_h)},gblur=sigma=1.5,"
        f"edgedetect=low=0.08:high=0.30,split=3[a][b][c];"
        f"[b]rotate={30}*PI/180:ow=iw:oh=ih:fillcolor=black[r1];"
        f"[c]rotate={-35}*PI/180:ow=iw:oh=ih:fillcolor=black[r2];"
        f"[a][r1]blend=all_mode=lighten[x1];"
        f"[x1][r2]blend=all_mode=lighten[x2];"
    )
    if not accumulate:
        return head + "[x2]null[out]"
    return (head
            + "nullsrc="
            + f"s={out_w}x{out_h}:r={C.VIDEO_FPS},format=gray,"
            + "geq=lum='if(lt(random(1),0.02),255,0)'[sp];"
            + "[x2]tblend=all_mode=lighten[st];"
            + "[st][sp]blend=all_mode=lighten[out]")


# ---------------------------------------------------------------------------
# Source helpers
# ---------------------------------------------------------------------------
def source_clip() -> Path:
    """Return the first video file in ``ascii/`` (the dancing-girl source)."""
    for pattern in ("*.mp4", "*.mov", "*.mkv", "*.webm"):
        found = sorted(glob.glob(str(C.IMAGES / pattern)))
        if found:
            return Path(found[0])
    raise SystemExit(f"no source video found in {C.IMAGES}")


def track_bpm() -> float:
    """The current track's BPM (from ``song.md``; falls back to config)."""
    match = re.search(r"^\s*bpm\s*:\s*([0-9.]+)", C.SONG.read_text(encoding="utf-8"), re.M)
    return float(match.group(1)) if match else C.BPM


def _loop_seconds() -> float:
    """The largest whole-beat loop length that fits the crop and divides the track.

    Keeps the edge/pollock loop aligned to the beat grid and tiling the video
    exactly (240 s / loop is an integer)."""
    beat = 60.0 / track_bpm()
    for beats in (8, 7, 6, 5, 4, 3, 2, 1):
        secs = beats * beat
        loops = C.DURATION / secs
        if secs <= C.GIRL_CROP_DURATION - 1e-6 and abs(loops - round(loops)) < 1e-3:
            return secs
    return 4 * beat


def _probe(path: Path) -> tuple[int, int, float]:
    """Return the first video stream's (width, height, fps)."""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height,r_frame_rate", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True).stdout.strip()
    w, h, rate = out.split(",")[:3]
    num, _, den = rate.partition("/")
    return int(w), int(h), float(num) / float(den or 1)


def _decode_crop(path: Path, vf: str, pix: str, w: int, h: int):
    """Decode ``GIRL_CROP_*`` seconds through *vf* as raw frames of *pix*."""
    raw = subprocess.run(
        ["ffmpeg", "-hide_banner", "-v", "error",
         "-ss", str(C.GIRL_CROP_START), "-t", str(C.GIRL_CROP_DURATION), "-i", str(path),
         "-vf", vf, "-pix_fmt", pix, "-f", "rawvideo", "-"],
        capture_output=True).stdout
    ch = 3 if pix == "rgb24" else 1
    n = len(raw) // (w * h * ch)
    return np.frombuffer(raw, np.uint8)[:n * w * h * ch].reshape(n, h, w, ch)


def _matte_over_black(frames: np.ndarray) -> np.ndarray:
    """Matte each frame with RVM, keep the main subject, return grey frames."""
    from .matte import RVMMatte, largest_component

    model = RVMMatte(C.GIRL_MODEL, downscale=C.GIRL_MATTE_DOWNSCALE)
    out = np.zeros(frames.shape[:3], np.uint8)
    for i, frame in enumerate(frames):
        alpha = model.matte(frame)
        keep = largest_component(alpha > 0.5)
        alpha = alpha * keep.astype(np.float32)
        out[i] = np.clip(frame.astype(np.float32).mean(axis=2) * alpha, 0, 255).astype(np.uint8)
    return out


def _expand(mask: np.ndarray, k: int) -> np.ndarray:
    """Binary dilation by *k* pixels (4-connected, no wraparound)."""
    out = mask
    for _ in range(k):
        p = np.pad(out, 1, mode="constant", constant_values=False)
        out = (p[1:-1, 1:-1] | p[:-2, 1:-1] | p[2:, 1:-1]
               | p[1:-1, :-2] | p[1:-1, 2:])
    return out


def _blue_mask(rgb: np.ndarray) -> np.ndarray:
    """Chroma-key the (blue) hair: pixels clearly bluer than red/green."""
    r, g, b = (rgb[..., i].astype(np.int16) for i in range(3))
    return (b > 70) & (b - r > 25) & (b - g > 15)


def _largest_blob(mask: np.ndarray) -> np.ndarray:
    """Boolean mask of the largest 4-connected blob (fine; small inputs only)."""
    h, w = mask.shape
    labels = np.zeros((h, w), np.int32)
    current = 0
    best_size, best_label = 0, 0
    for yy in range(h):
        for xx in range(w):
            if not mask[yy, xx] or labels[yy, xx]:
                continue
            current += 1
            size = 0
            stack = [(yy, xx)]
            labels[yy, xx] = current
            while stack:
                cy, cx = stack.pop()
                size += 1
                for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not labels[ny, nx]:
                        labels[ny, nx] = current
                        stack.append((ny, nx))
            if size > best_size:
                best_size, best_label = size, current
    return labels == best_label


def _eye_outline(frame: np.ndarray, subj: np.ndarray) -> np.ndarray | None:
    """Outline the eyes from the source: head box -> eye band -> darkest blobs.

    No ML: the head is the top of the subject, the eye band is a fixed fraction
    of it, and the eyes are the darkest blobs in the central face area."""
    h, w = subj.shape
    rows = np.where(subj.any(axis=1))[0]
    if rows.size == 0:
        return None
    y0, y1 = int(rows[0]), int(rows[-1])
    head = max(24, int(0.26 * (y1 - y0)))
    ya = y0 + int(0.40 * head)
    yb = y0 + int(0.64 * head)
    if yb - ya < 6:
        return None
    band = subj[ya:yb]
    cols = np.where(band.any(axis=0))[0]
    if cols.size < 10:
        return None
    # Restrict to the central face (skip the hair on the sides).
    cx0 = int(cols[0] + 0.22 * (cols[-1] - cols[0]))
    cx1 = int(cols[0] + 0.78 * (cols[-1] - cols[0]))
    face = np.zeros_like(band)
    face[:, cx0:cx1] = True
    lum = frame[ya:yb].mean(axis=2)
    region = band & face
    if region.sum() < 12:
        return None
    dark = region & (lum <= np.percentile(lum[region], 33))
    mid = (cx0 + cx1) // 2
    eyes = np.zeros_like(dark)
    for lo, hi in ((cx0, mid), (mid, cx1)):
        half = dark[:, lo:hi]
        if half.sum() >= 3:
            eyes[:, lo:hi] = _largest_blob(half)
    if eyes.sum() == 0:
        return None
    out = np.zeros((h, w), bool)
    out[ya:yb] = _expand(eyes, 2) & ~_expand(eyes, 1)     # a visible 2px ring
    return out


def _outline_sprites(frames: np.ndarray) -> np.ndarray:
    """Per-source-frame sprite: white silhouette outline + blue-keyed hair."""
    from .matte import RVMMatte, largest_component

    model = RVMMatte(C.GIRL_MODEL, downscale=C.GIRL_MATTE_DOWNSCALE)
    h, w = frames.shape[1:3]
    sprites = np.zeros((frames.shape[0], h, w, 3), np.uint8)
    for i, frame in enumerate(frames):
        alpha = model.matte(frame)
        fine = alpha > 0.5
        fine[:C.GIRL_TOP_MARGIN] = False              # drop the stage-light truss
        # Coarse component pick (drops the crowd), then the fine mask limited to
        # the subject so the outline follows the real silhouette.
        subj = fine & largest_component(fine, down=10, frac=0.55, dilate_px=2)
        outline = _expand(subj, 2) & ~subj            # silhouette boundary only
        hair = _blue_mask(frame) & _expand(subj, 3)   # hair on the subject only
        sprite = sprites[i]
        sprite[outline] = 255
        sprite[hair] = np.clip(frame[hair].astype(np.int16) * 1.15, 0, 255).astype(np.uint8)
        eyes = _eye_outline(frame, subj)
        if eyes is not None:
            sprite[eyes] = 255
    return sprites


def _encode_rgb(frames: np.ndarray, out: Path, out_h: int) -> None:
    """Encode an RGB frame array to H.264 at 16:9 (scaled from the sprite size)."""
    h, w = frames.shape[1:3]
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-v", "error", "-y",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(C.VIDEO_FPS),
         "-i", "-", "-vf", f"scale=1920:{out_h}:flags=lanczos",
         "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p",
         "-movflags", "+faststart", str(out)],
        input=frames.tobytes())


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
def build(look: str = "pollock", mode: str = "trail") -> tuple[Path, Path]:
    """Build the beat-locked loop (and its frame data).

    ``look`` is ``"pollock"``, ``"edge"`` or ``"outline"``. ``mode`` (pollock
    only) selects the paint accumulation (``reset``/``trail``/``build``).
    Returns ``(loop_mp4, frames_or_sprites_npy)``.
    """
    if look not in ("edge", "pollock", "outline"):
        raise SystemExit(f"unknown look '{look}' (use 'edge', 'pollock' or 'outline')")
    if look == "outline":
        return _build_outline()

    src = source_clip()
    w, h, fps = _probe(src)
    C.LOGS.mkdir(parents=True, exist_ok=True)

    if look == "pollock":
        grey = _decode_crop(src, f"scale={w}:{h},format=gray", "gray", w, h)[..., 0]
    else:
        rgb = _decode_crop(src, f"scale={w}:{h}", "rgb24", w, h)
        grey = _matte_over_black(rgb)
    if grey.shape[0] == 0:
        raise SystemExit(f"could not decode any frames from {src}")

    raw = C.LOGS / "girl_src.raw"           # native-size grey sequence
    raw.write_bytes(grey.tobytes())
    base = ["-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{w}x{h}",
            "-r", f"{fps:g}", "-i", str(raw)]
    n_frames = round(_loop_seconds() * C.VIDEO_FPS)

    # 1) frame stack consumed by the video build.
    if look == "pollock":
        stack_cmd = ["ffmpeg", "-hide_banner", "-v", "error", *base,
                     "-filter_complex", _pollock_filter(C.GIRL_FRAME_W, C.GIRL_FRAME_H, False),
                     "-map", "[out]", "-frames:v", str(n_frames)]
    else:
        stack_cmd = ["ffmpeg", "-hide_banner", "-v", "error", *base,
                     "-vf", f"{_fit(C.GIRL_FRAME_W, C.GIRL_FRAME_H)},{_EDGE}",
                     "-frames:v", str(n_frames)]
    proc = subprocess.run([*stack_cmd, "-pix_fmt", "gray", "-f", "rawvideo", "-"],
                          capture_output=True)
    buf = np.frombuffer(proc.stdout, np.uint8)
    stack = buf[:n_frames * C.GIRL_FRAME_H * C.GIRL_FRAME_W].reshape(
        n_frames, C.GIRL_FRAME_H, C.GIRL_FRAME_W)
    np.save(C.GIRL_FRAMES, stack)

    # 2) standalone deliverable at 1080p.
    loop = C.unique_path(C.GIRL_LOOP)
    if look == "pollock":
        ffmpeg(["-y", *base, "-filter_complex",
                _pollock_filter(C.VIDEO_W, C.VIDEO_H, True), "-map", "[out]",
                "-frames:v", str(n_frames), "-c:v", "libx264", "-preset", "slow",
                "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(loop)])
    else:
        ffmpeg(["-y", *base, "-vf", f"{_fit(C.VIDEO_W, C.VIDEO_H)},{_EDGE}",
                "-frames:v", str(n_frames), "-c:v", "libx264", "-preset", "slow",
                "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(loop)])
    return loop, C.GIRL_FRAMES


def _build_outline() -> tuple[Path, Path]:
    """Build the outline sprite set + a beat-synced pick, and a short loop."""
    src = source_clip()
    C.LOGS.mkdir(parents=True, exist_ok=True)

    frames = _decode_crop(
        src, f"{_fit(C.GIRL_FRAME_W, C.GIRL_FRAME_H)}", "rgb24",
        C.GIRL_FRAME_W, C.GIRL_FRAME_H)
    if frames.shape[0] == 0:
        raise SystemExit(f"could not decode any frames from {src}")
    sprites = _outline_sprites(frames)
    np.save(C.GIRL_SPRITES, sprites)

    # Beat-synced random picks across the whole track (deterministic).
    bpm = track_bpm()
    beat = 60.0 / bpm
    n_frames = round(C.DURATION * C.VIDEO_FPS)
    n_beats = int(np.ceil(C.DURATION / beat))
    rng = np.random.default_rng(20261012)
    per_beat = rng.integers(0, sprites.shape[0], size=n_beats)
    beat_of = np.minimum((np.arange(n_frames) / (C.VIDEO_FPS * beat)).astype(int), n_beats - 1)
    pick = per_beat[beat_of].astype(np.int32)
    np.save(C.GIRL_PICK, pick)

    # Standalone deliverable: the first 16 beats, encoded from the sprites.
    n_loop = int(round(16 * C.VIDEO_FPS * beat))
    loop = C.unique_path(C.GIRL_LOOP)
    _encode_rgb(sprites[pick[:n_loop]], loop, C.VIDEO_H)
    return loop, C.GIRL_SPRITES
