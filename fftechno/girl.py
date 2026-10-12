"""Girl pipeline: turn a song's source clip into the beat-locked video picture.

Generic: the song supplies the source/crop/look (``video.md``) and the style comes
from a :class:`~fftechno.looks.Look` strategy. This module only wires the shared
stages - decode -> optional matte -> look -> fit -> emit frame data + a standalone
loop - and holds no style-specific code.
"""

from __future__ import annotations

import glob
import subprocess
from pathlib import Path

import numpy as np

from . import config as C
from .looks import fit, get_look
from .proc import ffmpeg
from .song import Song


# ---------------------------------------------------------------------------
# Source helpers
# ---------------------------------------------------------------------------
def source_clip(song: Song) -> Path:
    """The song's source clip, or the first video in ``ascii/``."""
    configured = song.video().source_path()
    if configured and configured.exists():
        return configured
    for pattern in ("*.mp4", "*.mov", "*.mkv", "*.webm"):
        found = sorted(glob.glob(str(C.IMAGES / pattern)))
        if found:
            return Path(found[0])
    raise SystemExit(f"no source video found in {C.IMAGES}")


def _probe(path: Path) -> tuple[int, int, float]:
    out = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height,r_frame_rate",
            "-of",
            "csv=p=0",
            str(path),
        ],
        capture_output=True,
        text=True,
    ).stdout.strip()
    w, h, rate = out.split(",")[:3]
    num, _, den = rate.partition("/")
    return int(w), int(h), float(num) / float(den or 1)


def _decode_crop(
    src: Path, vf: str, pix: str, w: int, h: int, start: float, dur: float
) -> np.ndarray:
    raw = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-v",
            "error",
            "-ss",
            str(start),
            "-t",
            str(dur),
            "-i",
            str(src),
            "-vf",
            vf,
            "-pix_fmt",
            pix,
            "-f",
            "rawvideo",
            "-",
        ],
        capture_output=True,
    ).stdout
    ch = 3 if pix == "rgb24" else 1
    n = len(raw) // (w * h * ch)
    return np.frombuffer(raw, np.uint8)[: n * w * h * ch].reshape(n, h, w, ch)


def _loop_frames(song: Song) -> int:
    """Number of frames in the standalone loop (a whole number of beats)."""
    beat = 60.0 / song.bpm
    video = song.video()
    if video.loop_beats:
        return max(1, round(video.loop_beats * beat * C.VIDEO_FPS))
    for beats in (16, 12, 8, 7, 6, 5, 4, 3, 2, 1):
        secs = beats * beat
        loops = song.duration / secs
        if secs <= video.crop_duration - 1e-6 and abs(loops - round(loops)) < 1e-3:
            return max(1, round(secs * C.VIDEO_FPS))
    return max(1, round(8 * beat * C.VIDEO_FPS))


def _encode_rgb(frames: np.ndarray, out: Path) -> None:
    h, w = frames.shape[1:3]
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-v",
            "error",
            "-y",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-s",
            f"{w}x{h}",
            "-r",
            str(C.VIDEO_FPS),
            "-i",
            "-",
            "-vf",
            f"scale={C.VIDEO_W}:{C.VIDEO_H}:flags=lanczos",
            "-c:v",
            "libx264",
            "-preset",
            "slow",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(out),
        ],
        input=frames.tobytes(),
    )


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
def build(
    song: Song, look: str | None = None, mode: str | None = None
) -> tuple[Path, Path]:
    """Build the beat-locked picture data and a standalone loop for *song*.

    Returns ``(loop_mp4, data_npy)``; the MP4 gets a versioned name. ``mode`` is
    only a passthrough hint for the visualizer (see ``video.md``/``--mode``)."""
    video = song.video()
    look_name = look or video.look
    look_obj = get_look(
        look_name, {k[1]: v for k, v in video.params.items() if k[0] == look_name}
    )
    src = source_clip(song)
    w, h, fps = _probe(src)
    song.logs.mkdir(parents=True, exist_ok=True)

    if look_obj.emits == "sprites":
        return _build_sprites(song, look_obj, src)

    # --- stack looks (edge / pollock): grey frames -> ffmpeg -> .npy ----------
    if look_obj.needs_matte:
        from .matte import RVMMatte

        rgb = _decode_crop(
            src, f"scale={w}:{h}", "rgb24", w, h, video.crop_start, video.crop_duration
        )
        model = RVMMatte(C.GIRL_MODEL, downscale=C.GIRL_MATTE_DOWNSCALE)
        grey = np.zeros(rgb.shape[:3], np.uint8)
        for i, frame in enumerate(rgb):
            alpha = model.matte(frame)
            keep = _largest(frame.shape[:2], alpha)
            grey[i] = np.clip(
                frame.astype(np.float32).mean(axis=2) * alpha * keep, 0, 255
            ).astype(np.uint8)
    else:
        grey = _decode_crop(
            src,
            f"scale={w}:{h},format=gray",
            "gray",
            w,
            h,
            video.crop_start,
            video.crop_duration,
        )[..., 0]
    if grey.shape[0] == 0:
        raise SystemExit(f"could not decode any frames from {src}")

    raw = song.logs / "girl_src.raw"
    raw.write_bytes(grey.tobytes())
    base = [
        "-f",
        "rawvideo",
        "-pix_fmt",
        "gray",
        "-s",
        f"{w}x{h}",
        "-r",
        f"{fps:g}",
        "-i",
        str(raw),
    ]
    n_frames = _loop_frames(song)

    proc = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-v",
            "error",
            *base,
            "-filter_complex",
            look_obj.stack_filter(C.GIRL_FRAME_W, C.GIRL_FRAME_H),
            "-map",
            "[out]",
            "-frames:v",
            str(n_frames),
            "-pix_fmt",
            "gray",
            "-f",
            "rawvideo",
            "-",
        ],
        capture_output=True,
    )
    buf = np.frombuffer(proc.stdout, np.uint8)
    stack = buf[: n_frames * C.GIRL_FRAME_H * C.GIRL_FRAME_W].reshape(
        n_frames, C.GIRL_FRAME_H, C.GIRL_FRAME_W
    )
    np.save(song.girl_frames, stack)

    loop = C.unique_path(song.girl_loop)
    ffmpeg(
        [
            "-y",
            *base,
            "-filter_complex",
            look_obj.loop_filter(C.VIDEO_W, C.VIDEO_H),
            "-map",
            "[out]",
            "-frames:v",
            str(n_frames),
            "-c:v",
            "libx264",
            "-preset",
            "slow",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(loop),
        ]
    )
    return loop, song.girl_frames


def _largest(shape, alpha):
    """Subject keep-mask (largest blob) for the matte looks."""
    from .matte import largest_component

    return largest_component(alpha > 0.5).astype(np.float32)


def _build_sprites(song: Song, look_obj, src: Path) -> tuple[Path, Path]:
    """Sprite looks (outline): fitted RGB -> sprites + beat-synced pick."""
    from .matte import RVMMatte

    video = song.video()
    frames = _decode_crop(
        src,
        fit(C.GIRL_FRAME_W, C.GIRL_FRAME_H),
        "rgb24",
        C.GIRL_FRAME_W,
        C.GIRL_FRAME_H,
        video.crop_start,
        video.crop_duration,
    )
    if frames.shape[0] == 0:
        raise SystemExit(f"could not decode any frames from {src}")
    model = RVMMatte(C.GIRL_MODEL, downscale=C.GIRL_MATTE_DOWNSCALE)
    sprites = look_obj.sprites(frames, model.matte)
    np.save(song.girl_sprites, sprites)

    # Beat-synced random picks across the whole track (deterministic).
    beat = 60.0 / song.bpm
    n_frames = round(song.duration * C.VIDEO_FPS)
    n_beats = int(np.ceil(song.duration / beat))
    rng = np.random.default_rng(20261012)
    per_beat = rng.integers(0, sprites.shape[0], size=n_beats)
    beat_of = np.minimum(
        (np.arange(n_frames) / (C.VIDEO_FPS * beat)).astype(int), n_beats - 1
    )
    np.save(song.girl_pick, per_beat[beat_of].astype(np.int32))

    n_loop = _loop_frames(song)
    loop = C.unique_path(song.girl_loop)
    _encode_rgb(sprites[np.load(song.girl_pick)[:n_loop]], loop)
    return loop, song.girl_sprites
