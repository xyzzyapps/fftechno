"""Robust Video Matting (RVM) helper for isolating a subject in a video.

``MatteModel`` is the interface (an RGB frame -> a float alpha matte); ``RVMMatte``
implements it with RVM (``rvm_mobilenetv3_fp32.onnx``) driven by ``onnxruntime``.
RVM is recurrent, so frames are matted in order and the state is carried between
them - this keeps the matte temporally stable (no per-frame flicker).

``largest_component`` keeps only the biggest blob of a mask, which drops the
background crowd that RVM would otherwise also treat as foreground.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np


class MatteModel:
    """Interface: map a single RGB frame to a floating-point alpha matte.

    ``matte`` returns a ``(H, W)`` float32 array in ``[0, 1]``. Implementations
    may keep internal state between calls (RVM does), so frames must be fed in
    temporal order.
    """

    def matte(self, rgb: np.ndarray) -> np.ndarray:  # pragma: no cover - interface
        raise NotImplementedError


class RVMMatte(MatteModel):
    """RVM (Robust Video Matting) mobilenetv3, recurrent across frames."""

    def __init__(self, model_path: Path, downscale: float = 0.5,
                 providers: list[str] | None = None) -> None:
        import onnxruntime as ort  # imported lazily so audio-only builds stay light

        if not Path(model_path).exists():
            raise SystemExit(f"RVM model not found at {model_path}; see SPEC.md")
        self.session = ort.InferenceSession(
            str(model_path), providers=providers or ["CPUExecutionProvider"])
        self.downscale = np.array([downscale], np.float32)
        # Recurrent state, seeded at 1x1; the model resizes it on the first call.
        self.rec: list[np.ndarray] = [
            np.zeros((1, c, 1, 1), np.float32) for c in (16, 20, 40, 64)]

    def matte(self, rgb: np.ndarray) -> np.ndarray:
        """Return the alpha matte ``(H, W)`` float32 for one RGB frame."""
        src = (rgb.astype(np.float32) / 255.0).transpose(2, 0, 1)[None]
        out = self.session.run(None, {
            "src": src,
            "r1i": self.rec[0], "r2i": self.rec[1],
            "r3i": self.rec[2], "r4i": self.rec[3],
            "downsample_ratio": self.downscale,
        })
        self.rec = list(out[2:6])
        return out[1][0, 0]


def largest_component(mask: np.ndarray, down: int = 8, frac: float = 0.5,
                      dilate: int = 6) -> np.ndarray:
    """Return a boolean mask of the largest connected blob of *mask*.

    Labelling is done on a ``down``-times block-reduced copy (any-block mean
    ``>= frac``) so it is fast; the winning blob is then scaled back up and
    dilated by *dilate* pixels to keep soft edges.
    """
    h, w = mask.shape
    sh, sw = (h + down - 1) // down, (w + down - 1) // down
    pad = np.zeros((sh * down, sw * down), np.float32)
    pad[:h, :w] = mask
    small = pad.reshape(sh, down, sw, down).mean(axis=(1, 3)) >= frac

    labels = np.zeros((sh, sw), np.int32)
    current = 0
    best_size, best_label = 0, 0
    for y0 in range(sh):
        for x0 in range(sw):
            if not small[y0, x0] or labels[y0, x0]:
                continue
            current += 1
            size = 0
            stack = [(y0, x0)]
            labels[y0, x0] = current
            while stack:
                cy, cx = stack.pop()
                size += 1
                for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < sh and 0 <= nx < sw and small[ny, nx] and not labels[ny, nx]:
                        labels[ny, nx] = current
                        stack.append((ny, nx))
            if size > best_size:
                best_size, best_label = size, current

    big = np.repeat(np.repeat(labels == best_label, down, 0), down, 1)[:h, :w]
    keep = big.copy()
    for _ in range(dilate):
        keep = (keep | np.roll(keep, 1, 0) | np.roll(keep, -1, 0)
                | np.roll(keep, 1, 1) | np.roll(keep, -1, 1))
    return keep
