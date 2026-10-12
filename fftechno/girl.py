"""Dancing-girl visual: matte the source clip, then render a black-and-white
loop - either a clean **edge** drawing or an all-over **Pollock** painting.

Looks
-----
``edge`` (default when requested)
    RVM-matte the girl, keep only her (drops the crowd), and ``edgedetect`` a
    white line drawing on black.
``pollock``
    Use the **whole frame** (no matte): ``edgedetect`` thin lines, blend crossed
    rotated copies (gestures at several angles) and random splatter, for a
    tangled, all-over ink-on-paint look. The per-frame paint layer is stored in
    ``output/girl_frames.npy`` and *accumulated over time by the visualizer*
    (see ``mode``).

Pipeline
--------
1. Decode ``GIRL_CROP_START .. +GIRL_CROP_DURATION`` (2.0 s..5.0 s = 7 beats) at
   native size/fps.
2. ``edge``: matte with RVM, keep the largest blob, composite over black.
   ``pollock``: use the frame directly.
3. ffmpeg: resample to the video fps, fit to 16:9 with black bars, then the look
   chain (edge-detect / Pollock).
4. Write ``output/girl_frames.npy`` and a standalone ``output/girl_loop.mp4``.

Because 3.0 s = 7 beats = 1/80 of the 4:00 track, the loop tiles the video
exactly 80 times and always restarts on a beat.
"""

from __future__ import annotations

import glob
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


def _probe(path: Path) -> tuple[int, int, float]:
    """Return the first video stream's (width, height, fps)."""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height,r_frame_rate", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True).stdout.strip()
    w, h, rate = out.split(",")[:3]
    num, _, den = rate.partition("/")
    return int(w), int(h), float(num) / float(den or 1)


def _decoder(path: Path, w: int, h: int, start: float, dur: float, pix: str):
    """ffmpeg argv that decodes the crop as raw frames of format *pix*."""
    return ["ffmpeg", "-hide_banner", "-v", "error", "-ss", str(start), "-t", str(dur),
            "-i", str(path), "-pix_fmt", pix, "-f", "rawvideo", "-"]


def _decode_rgb(path: Path, w: int, h: int) -> np.ndarray:
    """Decode the crop as RGB frames ``(N, H, W, 3)`` (for matting)."""
    raw = subprocess.run(
        ["ffmpeg", "-hide_banner", "-v", "error",
         "-ss", str(C.GIRL_CROP_START), "-t", str(C.GIRL_CROP_DURATION), "-i", str(path),
         "-vf", f"scale={w}:{h}", "-pix_fmt", "rgb24", "-f", "rawvideo", "-"],
        capture_output=True).stdout
    n = len(raw) // (w * h * 3)
    return np.frombuffer(raw, np.uint8)[:n * w * h * 3].reshape(n, h, w, 3)


def _decode_grey(path: Path, w: int, h: int) -> np.ndarray:
    """Decode the crop as grey frames ``(N, H, W)`` (whole frame, no matte)."""
    raw = subprocess.run(
        ["ffmpeg", "-hide_banner", "-v", "error",
         "-ss", str(C.GIRL_CROP_START), "-t", str(C.GIRL_CROP_DURATION), "-i", str(path),
         "-vf", f"scale={w}:{h},format=gray", "-pix_fmt", "gray", "-f", "rawvideo", "-"],
        capture_output=True).stdout
    n = len(raw) // (w * h)
    return np.frombuffer(raw, np.uint8)[:n * w * h].reshape(n, h, w)


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


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
def build(look: str = "pollock", mode: str = "trail") -> tuple[Path, Path]:
    """Build the beat-locked B/W loop and its frame stack.

    ``look`` is ``"edge"`` (matte + line drawing) or ``"pollock"`` (whole-frame,
    tangled painting). ``mode`` (pollock only) selects how the visualizer
    accumulates the paint: ``reset`` (per loop), ``trail`` (decaying) or
    ``build`` (across the whole track). Returns ``(loop_mp4, frames_npy)``.
    """
    if look not in ("edge", "pollock"):
        raise SystemExit(f"unknown look '{look}' (use 'edge' or 'pollock')")
    src = source_clip()
    w, h, fps = _probe(src)
    C.LOGS.mkdir(parents=True, exist_ok=True)

    if look == "pollock":
        grey = _decode_grey(src, w, h)
    else:
        grey = _matte_over_black(_decode_rgb(src, w, h))
    if grey.shape[0] == 0:
        raise SystemExit(f"could not decode any frames from {src}")

    raw = C.LOGS / "girl_src.raw"           # native-size grey sequence
    raw.write_bytes(grey.tobytes())
    base = ["-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{w}x{h}",
            "-r", f"{fps:g}", "-i", str(raw)]

    n_frames = round(C.GIRL_LOOP_SECONDS * C.VIDEO_FPS)

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
