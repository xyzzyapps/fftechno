"""Looks: the style-specific visual transforms, as pluggable strategies.

The girl pipeline (``fftechno/girl.py``) is generic; it picks a :class:`Look` from
the song's ``video.md`` and this module supplies the only style-specific code.
Every look declares how it consumes the source (``needs_matte``), what it emits
(``emits``) and, for the video shader, whether it wants a paint accumulation
(``accumulation``).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable

import numpy as np

from . import config as C
from .matte import dilate, largest_component


def fit(out_w: int, out_h: int) -> str:
    """Resample to the video fps and letterbox into a 16:9 frame."""
    return (
        f"fps={C.VIDEO_FPS},scale=-2:{out_h}:flags=lanczos,"
        f"pad={out_w}:{out_h}:(ow-iw)/2:(oh-ih)/2:black"
    )


# ---------------------------------------------------------------------------
# Look interface
# ---------------------------------------------------------------------------
class Look(ABC):
    """A style: how to turn the cropped source frames into the video picture."""

    name: str = ""
    needs_matte: bool = False  # run RVM matting before the transform?
    emits: str = "stack"  # "stack" (grey npy) | "sprites" (RGB npy + pick)
    accumulation: str | None = None  # shader hint for stack looks
    decode: str = "native"  # "native" or "fitted" (half the output size)

    def configure(self, params: dict[str, str]) -> None:
        """Apply per-song overrides from ``video.md`` (optional)."""

    def decode_filter(self, out_w: int, out_h: int) -> str:
        """The ffmpeg filter that decodes the source into the fitted frame."""
        return fit(out_w, out_h)

    @abstractmethod
    def stack_filter(self, out_w: int, out_h: int) -> str:
        """A ``-filter_complex`` body ending in ``[out]`` (for ``emits == 'stack'``)."""

    def loop_filter(self, out_w: int, out_h: int) -> str:
        """Filter for the standalone loop (defaults to the stack filter)."""
        return self.stack_filter(out_w, out_h)

    def sprites(self, frames: np.ndarray, model) -> np.ndarray:
        """Return RGB sprites (for ``emits == 'sprites'``)."""
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Concrete looks
# ---------------------------------------------------------------------------
class EdgeLook(Look):
    """A clean white line drawing of the matted subject."""

    name = "edge"
    needs_matte = True
    _EDGE = "edgedetect=low=0.08:high=0.25"

    def stack_filter(self, out_w: int, out_h: int) -> str:
        return f"[0:v]{fit(out_w, out_h)},{self._EDGE}[out]"


class PollockLook(Look):
    """An all-over abstract "painting" from whole-frame edges."""

    name = "pollock"
    needs_matte = False
    accumulation = "trail"

    def _filter(self, out_w: int, out_h: int, accumulate: bool) -> str:
        head = (
            f"[0:v]{fit(out_w, out_h)},gblur=sigma=1.5,"
            f"edgedetect=low=0.08:high=0.30,split=3[a][b][c];"
            f"[b]rotate=30*PI/180:ow=iw:oh=ih:fillcolor=black[r1];"
            f"[c]rotate=-35*PI/180:ow=iw:oh=ih:fillcolor=black[r2];"
            f"[a][r1]blend=all_mode=lighten[x1];"
            f"[x1][r2]blend=all_mode=lighten[x2];"
        )
        if not accumulate:
            return head + "[x2]null[out]"
        return (
            head
            + f"nullsrc=s={out_w}x{out_h}:r={C.VIDEO_FPS},format=gray,"
            + "geq=lum='if(lt(random(1),0.02),255,0)'[sp];"
            + "[x2]tblend=all_mode=lighten[st];"
            + "[st][sp]blend=all_mode=lighten[out]"
        )

    def stack_filter(self, out_w: int, out_h: int) -> str:
        return self._filter(out_w, out_h, False)

    def loop_filter(self, out_w: int, out_h: int) -> str:
        return self._filter(out_w, out_h, True)


class OutlineLook(Look):
    """Only the subject's silhouette outline; the blue hair is chroma-keyed."""

    name = "outline"
    needs_matte = True
    emits = "sprites"
    decode = "fitted"
    top_margin = 70  # rows ignored at the top (e.g. a light truss)
    hair_gain = 1.15

    def configure(self, params: dict[str, str]) -> None:
        if "top_margin" in params:
            self.top_margin = int(params["top_margin"])
        if "hair_gain" in params:
            self.hair_gain = float(params["hair_gain"])

    def stack_filter(self, out_w: int, out_h: int) -> str:  # pragma: no cover
        raise NotImplementedError("outline emits sprites, not a stack")

    def sprites(
        self, frames: np.ndarray, model: Callable[[np.ndarray], np.ndarray]
    ) -> np.ndarray:
        h, w = frames.shape[1:3]
        sprites = np.zeros((frames.shape[0], h, w, 3), np.uint8)
        for i, frame in enumerate(frames):
            alpha = model(frame)
            fine = alpha > 0.5
            fine[: self.top_margin] = False
            subj = fine & largest_component(fine, down=10, frac=0.55, dilate_px=2)
            outline = dilate(subj, 2) & ~subj
            hair = _blue_mask(frame) & dilate(subj, 3)
            sprite = sprites[i]
            sprite[outline] = 255
            sprite[hair] = np.clip(
                frame[hair].astype(np.int16) * self.hair_gain, 0, 255
            ).astype(np.uint8)
        return sprites


class PhotoLook(Look):
    """A still image as the picture, full colour.

    ``framing`` decides how the image meets the frame: ``fit`` keeps the whole
    image and letterboxes it on black (good for a wide frame); ``fill`` scales it
    to cover the frame and centre-crops the overflow (good for a portrait photo in
    a vertical frame - no black bars). A fraction of the bottom can be trimmed
    (``crop_bottom``), e.g. to drop a watermark. ``focus`` names the vertical
    fraction of the image that must land in the middle of the frame, and
    ``shift_x``/``shift_y`` nudge the subject within the frame (output pixels).
    """

    name = "photo"
    needs_matte = False
    emits = "sprites"
    decode = "fitted"
    crop_bottom = 0.0  # fraction of the image height trimmed off the bottom
    crop_right = 0.0  # fraction of the image width trimmed off the right
    framing = "fit"  # "fit" (letterbox) | "fill" (cover + centre crop)
    focus: float | None = None  # vertical fraction to centre, e.g. 0.32 = the nose
    shift_x = 0.0  # move the subject in the frame, in output pixels (right = +)
    shift_y = 0.0  # ... and down = +

    def configure(self, params: dict[str, str]) -> None:
        if "crop_bottom" in params:
            self.crop_bottom = float(params["crop_bottom"])
        if "crop_right" in params:
            self.crop_right = float(params["crop_right"])
        if "focus" in params:
            self.focus = float(params["focus"])
        if "shift_x" in params:
            self.shift_x = float(params["shift_x"])
        if "shift_y" in params:
            self.shift_y = float(params["shift_y"])
        if "framing" in params:
            framing = params["framing"].strip().lower()
            if framing not in ("fit", "fill"):
                raise SystemExit(
                    f"photo: framing must be 'fit' or 'fill' (got '{framing}')"
                )
            self.framing = framing

    def _focus_crop(self, out_w: int, out_h: int) -> str:
        """Crop the largest target-aspect window centred on ``focus``.

        ``focus`` is the vertical fraction of the (bottom-trimmed) image that must
        land in the middle of the frame - e.g. the nose. The window is symmetric
        about it and as large as the aspect and the image allow, so the framing
        stays as wide as possible.
        """
        assert self.focus is not None
        aspect = out_w / out_h
        f = min(max(self.focus, 0.001), 0.999)
        room = f"2*{min(f, 1.0 - f):.6f}*ih"  # largest symmetric window that fits
        width = f"min(iw,{aspect:.6f}*min(ih,{room}))"
        height = f"min(ih,min({1 / aspect:.6f}*iw,{room}))"
        # `shift_*` moves the *subject*, so the window moves the other way: pushing
        # her right means starting the crop further left, and vice versa.
        dx = self.shift_x / out_w
        dy = self.shift_y / out_h
        return (
            f"crop=w='{width}':h='{height}':"
            f"x='max(0,(iw-ow)/2-{dx:.6f}*ow)':"
            f"y='max(0,{f:.6f}*ih-oh/2-{dy:.6f}*oh)'"
        )

    def decode_filter(self, out_w: int, out_h: int) -> str:
        parts = [f"fps={C.VIDEO_FPS}"]
        if self.crop_bottom:
            parts.append(f"crop=iw:ih*{max(0.0, 1.0 - self.crop_bottom):.4f}:0:0")
        if self.crop_right:
            parts.append(f"crop=iw*{max(0.0, 1.0 - self.crop_right):.4f}:ih:0:0")
        if self.framing == "fill":
            if self.focus is None:
                parts.append(
                    f"scale={out_w}:{out_h}:force_original_aspect_ratio=increase"
                    ":flags=lanczos"
                )
                parts.append(
                    f"crop={out_w}:{out_h}:"
                    f"(iw-ow)/2-{self.shift_x / out_w:.6f}*ow:"
                    f"(ih-oh)/2-{self.shift_y / out_h:.6f}*oh"
                )
            else:
                parts.append(self._focus_crop(out_w, out_h))
                parts.append(f"scale={out_w}:{out_h}:flags=lanczos")
        else:
            parts.append(f"scale=-2:{out_h}:flags=lanczos")
            parts.append(f"pad={out_w}:{out_h}:(ow-iw)/2:(oh-ih)/2:black")
        return ",".join(parts)

    def stack_filter(self, out_w: int, out_h: int) -> str:  # pragma: no cover
        raise NotImplementedError("photo emits sprites, not a stack")

    def sprites(self, frames: np.ndarray, model=None) -> np.ndarray:
        """A single frame: the still, fitted, colour preserved."""
        if frames.shape[0] == 0:
            raise SystemExit("photo: could not decode the source image")
        return np.asarray(frames[:1]).copy()


def _blue_mask(rgb: np.ndarray) -> np.ndarray:
    """Chroma-key the (blue) hair: pixels clearly bluer than red/green."""
    r, g, b = (rgb[..., i].astype(np.int16) for i in range(3))
    return (b > 70) & (b - r > 25) & (b - g > 15)


LOOKS: dict[str, Look] = {
    look.name: look for look in (EdgeLook(), PollockLook(), OutlineLook(), PhotoLook())
}


def get_look(name: str, params: dict[str, str] | None = None) -> Look:
    """Return the named look (a fresh copy configured with *params*)."""
    if name not in LOOKS:
        raise SystemExit(f"unknown look '{name}' (use: {', '.join(LOOKS)})")
    look = type(LOOKS[name])()
    if params:
        look.configure(params)
    return look
