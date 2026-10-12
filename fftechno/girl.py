"""Dancing-girl visual: matte the source clip, edge-detect, and build a
beat-locked black-and-white loop.

Pipeline
--------
1. Decode ``GIRL_CROP_START .. +GIRL_CROP_DURATION`` seconds of the first video
   in ``ascii/`` at its native size and frame rate.
2. Matte each frame with RVM (temporally stable), keep only the largest blob
   (drops the crowd), and composite the subject over black.
3. ffmpeg: resample to the video fps, fit to 16:9 with black bars, ``edgedetect``
   (white on black).
4. Write ``output/girl_frames.npy`` (a compact frame stack for the video build)
   and a standalone ``output/girl_loop.mp4``.

The crop is ``GIRL_LOOP_BEATS`` beats long at the project BPM, so the loop is
exactly a whole number of beats and tiles the track on the beat grid.
"""

from __future__ import annotations

import glob
import subprocess
from pathlib import Path

import numpy as np

from . import config as C
from .matte import RVMMatte, largest_component
from .proc import ffmpeg

_EDGE = "edgedetect=low=0.08:high=0.25"


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
    fps = float(num) / float(den or 1)
    return int(w), int(h), fps


def _decode(path: Path, w: int, h: int, start: float, dur: float) -> np.ndarray:
    """Decode ``dur`` seconds from *start* as RGB frames ``(N, H, W, 3)``."""
    raw = subprocess.run(
        ["ffmpeg", "-hide_banner", "-v", "error", "-ss", str(start), "-t", str(dur),
         "-i", str(path), "-vf", f"scale={w}:{h}", "-pix_fmt", "rgb24",
         "-f", "rawvideo", "-"],
        capture_output=True).stdout
    n = len(raw) // (w * h * 3)
    return np.frombuffer(raw, np.uint8)[:n * w * h * 3].reshape(n, h, w, 3)


def _matte_over_black(frames: np.ndarray) -> np.ndarray:
    """Matte each frame with RVM, keep the main subject, return grey frames."""
    model = RVMMatte(C.GIRL_MODEL, downscale=C.GIRL_MATTE_DOWNSCALE)
    out = np.zeros(frames.shape[:3], np.uint8)
    for i, frame in enumerate(frames):
        alpha = model.matte(frame)
        keep = largest_component(alpha > 0.5)
        alpha = alpha * keep.astype(np.float32)
        grey = frame.astype(np.float32).mean(axis=2) * alpha
        out[i] = np.clip(grey, 0, 255).astype(np.uint8)
    return out


def _fit(out_w: int, out_h: int) -> str:
    """Resample to the video fps, fit a 16:9 frame with black bars, edge-detect."""
    return (f"fps={C.VIDEO_FPS},scale=-2:{out_h}:flags=lanczos,"
            f"pad={out_w}:{out_h}:(ow-iw)/2:(oh-ih)/2:black,{_EDGE}")


def build() -> tuple[Path, Path]:
    """Build the beat-locked B/W girl loop and its frame stack.

    Returns ``(loop_mp4, frames_npy)``; the MP4 gets a versioned name so old
    renders are preserved."""
    src = source_clip()
    w, h, fps = _probe(src)
    C.LOGS.mkdir(parents=True, exist_ok=True)

    frames = _decode(src, w, h, C.GIRL_CROP_START, C.GIRL_CROP_DURATION)
    if frames.shape[0] == 0:
        raise SystemExit(f"could not decode any frames from {src}")
    grey = _matte_over_black(frames)

    raw = C.LOGS / "girl_grey.raw"          # native-size grey sequence (input)
    raw.write_bytes(grey.tobytes())
    base = ["-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{w}x{h}",
            "-r", f"{fps:g}", "-i", str(raw)]

    # 1) compact stack for the video build (fit 960x540, edge-detected).
    n_frames = round(C.GIRL_LOOP_SECONDS * C.VIDEO_FPS)
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-v", "error", *base, "-vf", _fit(C.GIRL_FRAME_W, C.GIRL_FRAME_H),
         "-frames:v", str(n_frames), "-pix_fmt", "gray", "-f", "rawvideo", "-"],
        capture_output=True)
    buf = np.frombuffer(proc.stdout, np.uint8)
    stack = buf[:n_frames * C.GIRL_FRAME_H * C.GIRL_FRAME_W].reshape(
        n_frames, C.GIRL_FRAME_H, C.GIRL_FRAME_W)
    np.save(C.GIRL_FRAMES, stack)

    # 2) standalone deliverable, upscaled to 1080p (crisper edges).
    loop = C.unique_path(C.GIRL_LOOP)
    ffmpeg(["-y", *base, "-vf", _fit(C.VIDEO_W, C.VIDEO_H), "-t", f"{C.GIRL_LOOP_SECONDS:.6f}",
            "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", str(loop)])
    return loop, C.GIRL_FRAMES
