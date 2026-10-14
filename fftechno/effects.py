"""Effects: the pluggable visual treatment chain (``source -> effects -> encode``).

A :class:`~fftechno.looks.Look` produces the base picture; the effects named in a
song's ``video.md`` then draw or shade on top of it, in order. There are two tiers:

* ``paint`` - numpy, per frame, on the low-res frame (960x540): geometry such as
  squares, grids or scanline bands. A paint effect can also read the per-instrument
  audio envelopes (see :func:`normalise` / :func:`follower`).
* ``shader`` - a GLSL snippet spliced into the vs-placebo shader (per pixel at
  1920x1080): grain, vignette, glitch, chromatic aberration, ...

Adding an effect is one subclass here plus a name in a song's ``video.md``:

    effects: squares, grain

and, if it takes knobs, an ``| effect | key | value |`` row in the song's
``video.md`` (the ``## Effect Parameters`` table).

The default chain reproduces the original hand-written shader (grain + vignette +
kick flash + kick glitch), so songs that do not name any effects render unchanged.
"""

from __future__ import annotations

import math
import os
import wave
from abc import ABC
from dataclasses import dataclass, field
from typing import ClassVar

import numpy as np

# The chain used when a song's video.md does not name one (the original shader).
DEFAULT_CHAIN: tuple[str, ...] = ("kick_flash", "vignette", "grain", "kick_glitch")


# ---------------------------------------------------------------------------
# Signal helpers (shared by paint effects)
# ---------------------------------------------------------------------------
def normalise(env: np.ndarray, hi_pc: float = 99.0) -> np.ndarray:
    """Scale a raw envelope to 0..1 using its high percentile."""
    hi = float(np.percentile(env, hi_pc)) + 1e-9
    return np.clip(np.asarray(env, np.float32) / hi, 0.0, 1.0)


def follower(env: np.ndarray, tau: float, fps: int) -> np.ndarray:
    """Fast attack, exponential release (``tau`` seconds) - the "vibration" signal.

    A hit jumps the output to the envelope value; it then decays with time
    constant *tau*, so a square keeps moving for a moment after each hit.
    """
    out = np.zeros(len(env), np.float32)
    k = 1.0 - 1.0 / max(fps * tau, 1.0)
    y = 0.0
    for i, v in enumerate(env):
        y = max(float(v), y * k)
        out[i] = y
    return out


def rms_envelope(path, n_frames: int, fps: int) -> np.ndarray:
    """Per-frame RMS of a 16-bit PCM wav (one instrument's gain-applied envelope)."""
    env = np.zeros(n_frames, np.float32)
    try:
        with wave.open(str(path), "rb") as wf:
            sr, nch, n = wf.getframerate(), wf.getnchannels(), wf.getnframes()
            data = np.frombuffer(wf.readframes(n), dtype="<i2")
    except Exception:
        return env
    mono = data.astype(np.float32).reshape(-1, nch).mean(axis=1) / 32768.0
    hop = max(1, sr // fps)
    for i in range(min(n_frames, len(mono) // hop)):
        seg = mono[i * hop : (i + 1) * hop]
        env[i] = float(np.sqrt(np.mean(seg**2))) if seg.size else 0.0
    return env


def load_envelopes(directory, names, n_frames: int, fps: int) -> dict:
    """``{instrument: per-frame RMS}`` for each ``<stem>.wav`` prepared by video.py."""
    return {
        name: rms_envelope(os.path.join(directory, f"{name}.wav"), n_frames, fps)
        for name in names
    }


# ---------------------------------------------------------------------------
# Effect interface
# ---------------------------------------------------------------------------
class Effect(ABC):
    """One selectable treatment. Subclasses set ``name``/``tier``/``defaults``."""

    name: str = ""
    tier: str = "shader"  # "shader" | "paint"
    uses_strip: bool = False  # does its GLSL read the audio data strip?
    defaults: ClassVar[dict[str, str]] = {}

    def __init__(self, params: dict[str, str] | None = None) -> None:
        self.params: dict[str, str] = {**self.defaults, **(params or {})}
        # Instruments this effect wants envelopes for (filled by build_chain).
        self.required: tuple[str, ...] = ()

    # --- parameter accessors ------------------------------------------------
    def f(self, key: str, fallback: float = 0.0) -> float:
        """A float parameter (falls back if missing or unparseable)."""
        try:
            return float(self.params.get(key, fallback))
        except (TypeError, ValueError):
            return float(fallback)

    def lst(self, key: str, fallback: tuple[str, ...] = ()) -> list[str]:
        """A ``|``-separated list parameter."""
        raw = self.params.get(key)
        return [t for t in raw.split("|") if t] if raw else list(fallback)

    # --- hooks --------------------------------------------------------------
    def required_instruments(self, stems: list[str]) -> tuple[str, ...]:
        """Which of the song's stems this effect needs envelopes for."""
        return ()

    def prepare(self, env: dict[str, np.ndarray], fps: int) -> None:
        """Precompute per-frame parameter arrays from the envelopes."""

    def paint(self, ctx: PaintCtx) -> None:
        """Draw onto the low-res frame (``tier == 'paint'``)."""

    def glsl_helpers(self) -> str:
        """GLSL functions this effect needs (``tier == 'shader'``)."""
        return ""

    def glsl_apply(self) -> str:
        """GLSL statements spliced into ``hook()`` (``tier == 'shader'``)."""
        return ""


@dataclass
class PaintCtx:
    """What a paint effect is handed for one frame (YUV444P16, 16-bit planes)."""

    luma: np.ndarray  # (H, W) uint16, 65535 = white
    u: np.ndarray
    v: np.ndarray
    index: int
    fps: int
    env: dict[str, np.ndarray] = field(default_factory=dict)

    @property
    def t(self) -> float:
        return self.index / self.fps

    @property
    def size(self) -> tuple[int, int]:
        """(width, height) of the frame."""
        return (self.luma.shape[1], self.luma.shape[0])

    def white(self, mask: np.ndarray, level: float = 1.0) -> None:
        """Paint *mask* as neutral white at *level* (0..1)."""
        if not mask.any():
            return
        self.luma[mask] = np.uint16(np.clip(level, 0.0, 1.0) * 65535)
        self.u[mask] = 128 * 257
        self.v[mask] = 128 * 257


# ---------------------------------------------------------------------------
# Shader-tier effects (per pixel, GLSL at 1920x1080)
# ---------------------------------------------------------------------------
class KickFlash(Effect):
    """Whole-picture brightness lift on every kick (reads the data strip)."""

    name = "kick_flash"
    uses_strip = True
    defaults: ClassVar[dict[str, str]] = {"base": "1.02", "gain": "0.9"}

    def glsl_apply(self) -> str:
        return f"    col *= ({self.f('base', 1.02):g} + kick*{self.f('gain', 0.9):g});"


class Vignette(Effect):
    """Gentle radial darkening towards the frame edge."""

    name = "vignette"
    defaults: ClassVar[dict[str, str]] = {"amount": "0.35"}

    def glsl_apply(self) -> str:
        return f"    col *= 1.0 - {self.f('amount', 0.35):g}*r;"


class Grain(Effect):
    """Per-pixel film grain."""

    name = "grain"
    defaults: ClassVar[dict[str, str]] = {"amount": "0.03"}

    def glsl_apply(self) -> str:
        return f"    col += (random - 0.5)*{self.f('amount', 0.03):g};"


class KickGlitch(Effect):
    """A one-frame horizontal glitch burst on hard kicks."""

    name = "kick_glitch"
    uses_strip = True
    defaults: ClassVar[dict[str, str]] = {
        "threshold": "0.78",
        "gain": "1.30",
        "amount": "0.12",
    }

    def glsl_helpers(self) -> str:
        return "float hash(float n){ return fract(sin(n)*43758.5453); }"

    def glsl_apply(self) -> str:
        return (
            f"    if(step({self.f('threshold', 0.78):g}, kick) > 0.5){{\n"
            f"        col = col*{self.f('gain', 1.3):g} "
            f"+ (hash(floor(t*30.0)) - 0.5)*{self.f('amount', 0.12):g};\n"
            "    }"
        )


# ---------------------------------------------------------------------------
# Paint-tier effects (per frame, numpy)
# ---------------------------------------------------------------------------
# Which parameter of a square an instrument drives, and the draw order.
ROLES: dict[str, str] = {
    # The kick's square is the outermost, so at its size it has no room left to
    # grow inside the frame: it pulses by *thickening* instead.
    "kick": "thickness",
    "bass": "drift",
    "hat": "thickness",
    "ohat": "rotate",
    "snare": "knock",
    "rim": "size",  # the ring pings by growing (a blink would need dimming)
}
ROLE_CYCLE: tuple[str, ...] = ("size", "drift", "thickness", "rotate", "knock", "flash")
SQUARE_ORDER: tuple[str, ...] = ("kick", "bass", "hat", "ohat", "snare", "rim")


class Squares(Effect):
    """White outline squares - one per instrument - that vibrate with the track.

    Each square is drawn only while its instrument is audible (a slow release
    follower over the instrument's envelope), so the pattern assembles itself as
    the arrangement builds; while muted it is hidden rather than dimmed. One square
    parameter per square is driven by its instrument: size, vertical drift, line
    thickness, rotation, a sideways knock or a brightness flash (see
    :data:`ROLES`). Instruments listed in the ``circles`` parameter are drawn as a
    ring instead of a square - the rim shot is a circle at the centre of the
    pattern by default.
    """

    name = "squares"
    tier = "paint"
    defaults: ClassVar[dict[str, str]] = {
        "max_half": "230",  # half-size of the outermost (first) square, low-res px
        "step": "34",  # each following square is this much smaller
        "halves": "",  # explicit half-sizes, in instrument order (overrides the above)
        "skip": "vox",  # instruments to leave out of the pattern
        "thickness": "2",  # outline width, low-res px
        "circles": "rim",  # instruments drawn as a ring instead of a square
        "swell": "0.55",  # "size" response (fraction of the half-size)
        "drift": "30",  # "drift" response (low-res px)
        "rotate": "0.35",  # "rotate" response (radians)
        "knock": "16",  # "knock" response (low-res px)
        "thick_gain": "2.5",  # "thickness" response (factor)
        "level": "0.85",  # outline brightness (0..1); also the flash's dim end
        "presence": "3.0",  # seconds a square lingers after its last hit
        "presence_hi": "0.15",  # follower value that means "fully present"
        "presence_on": "0.5",  # show/hide threshold on that presence (on/off)
        "decay": "0.22",  # envelope release (seconds)
    }

    def required_instruments(self, stems: list[str]) -> tuple[str, ...]:
        skip = set(self.lst("skip", ("vox",)))  # the voice is on screen already
        order = [s for s in SQUARE_ORDER if s in stems and s not in skip]
        order += [s for s in sorted(stems) if s not in order and s not in skip]
        return tuple(order)

    # --- setup --------------------------------------------------------------
    def prepare(self, env: dict[str, np.ndarray], fps: int) -> None:
        self._names = list(self.required)
        self._roles = [
            ROLES.get(n, ROLE_CYCLE[i % len(ROLE_CYCLE)])
            for i, n in enumerate(self._names)
        ]
        circles = set(self.lst("circles", ("rim",)))
        self._shapes = ["circle" if n in circles else "square" for n in self._names]
        self._vib = [
            follower(normalise(env[n]), self.f("decay", 0.22), fps) for n in self._names
        ]
        hi = max(self.f("presence_hi", 0.15), 1e-6)
        self._alpha = [
            np.clip(
                follower(normalise(env[n]), self.f("presence", 3.0), fps) / hi, 0, 1
            )
            for n in self._names
        ]
        max_half, step = self.f("max_half", 230.0), self.f("step", 34.0)
        sizes = [max(8.0, float(v)) for v in self.lst("halves")]
        if len(sizes) >= len(self._names):
            self._half = sizes[: len(self._names)]
        else:  # a uniform ladder (largest first) when no explicit sizes are given
            self._half = [
                max(8.0, max_half - i * step) for i in range(len(self._names))
            ]
        self._grid: np.ndarray | None = None
        self._cap: float | None = None  # frame-fitted half-size limit (set in paint)

    # --- drawing ------------------------------------------------------------
    def paint(self, ctx: PaintCtx) -> None:
        h, w = ctx.luma.shape
        if self._grid is None or self._grid.shape[1:] != (h, w):
            self._grid = np.indices((h, w), dtype=np.float32)
            # Never let a square grow past the frame: its edges would be clipped
            # into stray full-width lines.
            self._cap = 0.5 * min(w, h) - self.f("thickness", 2.0) - 2.0
        cy0, cx0 = h * 0.5, w * 0.5
        i = ctx.index
        for k in range(len(self._names)):
            # Presence is on/off: a square is drawn full white while its
            # instrument is audible and hidden (not dimmed) the rest of the time.
            if float(self._alpha[k][i]) <= self.f("presence_on", 0.5):
                continue
            v = float(self._vib[k][i])
            role = self._roles[k]
            half = min(
                (
                    self._half[k] * (1.0 + self.f("swell") * v)
                    if role == "size"
                    else self._half[k]
                ),
                self._cap,
            )
            thick = self.f("thickness", 2.0)
            if role == "thickness":
                thick *= 1.0 + self.f("thick_gain", 2.5) * v
            ang = self.f("rotate", 0.35) * v if role == "rotate" else 0.0
            cy = cy0 + (
                self.f("drift", 30.0) * (v - 0.5) * 2.0 if role == "drift" else 0.0
            )
            cx = cx0 + (self.f("knock", 16.0) * v if role == "knock" else 0.0)
            level = self.f("level", 0.85)
            if role == "flash":
                level = level + (1.0 - level) * v
            if self._shapes[k] == "circle":
                self._ring(ctx, cx, cy, half, thick, level)
            else:
                self._frame(ctx, cx, cy, half, ang, thick, level)

    def _stamp(self, ctx: PaintCtx, box, mask, level: float) -> None:
        """Write *mask* as neutral white at *level* inside *box* (x0, y0, x1, y1)."""
        if not mask.any():
            return
        x0, y0, x1, y1 = box
        ctx.luma[y0:y1, x0:x1][mask] = np.uint16(np.clip(level, 0.0, 1.0) * 65535)
        ctx.u[y0:y1, x0:x1][mask] = 128 * 257
        ctx.v[y0:y1, x0:x1][mask] = 128 * 257

    def _frame(
        self,
        ctx: PaintCtx,
        cx: float,
        cy: float,
        half: float,
        ang: float,
        thick: float,
        level: float,
    ) -> None:
        """Rasterise one rotated square outline, restricted to its bounding box."""
        h, w = ctx.luma.shape
        pad = thick + 2.0
        x0 = max(0, int(cx - half - pad))
        x1 = min(w, int(cx + half + pad) + 1)
        y0 = max(0, int(cy - half - pad))
        y1 = min(h, int(cy + half + pad) + 1)
        if x1 <= x0 or y1 <= y0:
            return
        yy, xx = self._grid
        dx = xx[y0:y1, x0:x1] - cx
        dy = yy[y0:y1, x0:x1] - cy
        if ang:
            c, s = math.cos(ang), math.sin(ang)
            rx = dx * c + dy * s
            ry = -dx * s + dy * c
        else:
            rx, ry = dx, dy
        ax, ay = np.abs(rx), np.abs(ry)
        mask = ((np.abs(ax - half) <= thick) & (ay <= half)) | (
            (np.abs(ay - half) <= thick) & (ax <= half)
        )
        self._stamp(ctx, (x0, y0, x1, y1), mask, level)

    def _ring(
        self,
        ctx: PaintCtx,
        cx: float,
        cy: float,
        radius: float,
        thick: float,
        level: float,
    ) -> None:
        """Rasterise one circle outline, restricted to its bounding box."""
        h, w = ctx.luma.shape
        pad = thick + 2.0
        x0 = max(0, int(cx - radius - pad))
        x1 = min(w, int(cx + radius + pad) + 1)
        y0 = max(0, int(cy - radius - pad))
        y1 = min(h, int(cy + radius + pad) + 1)
        if x1 <= x0 or y1 <= y0:
            return
        yy, xx = self._grid
        dist = np.hypot(xx[y0:y1, x0:x1] - cx, yy[y0:y1, x0:x1] - cy)
        self._stamp(ctx, (x0, y0, x1, y1), np.abs(dist - radius) <= thick, level)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
EFFECTS: dict[str, type[Effect]] = {
    cls.name: cls for cls in (KickFlash, Vignette, Grain, KickGlitch, Squares)
}


def build_chain(
    names: list[str] | tuple[str, ...],
    params: dict[tuple[str, str], str] | None = None,
    stems: list[str] | None = None,
) -> list[Effect]:
    """Instantiate *names* in order, with per-effect params and required stems.

    ``params`` is the song's ``(name, key) -> value`` map (looks and effects share
    the ``## Parameters`` table). Unknown names raise.
    """
    stems = list(stems or [])
    chain: list[Effect] = []
    for name in names:
        if name not in EFFECTS:
            raise SystemExit(
                f"unknown effect '{name}' (use: {', '.join(sorted(EFFECTS))})"
            )
        effect = EFFECTS[name](
            {k[1]: v for k, v in (params or {}).items() if k[0] == name}
        )
        effect.required = effect.required_instruments(stems)
        chain.append(effect)
    return chain


def required_instruments(chain: list[Effect]) -> list[str]:
    """Every instrument the chain wants, in first-seen order."""
    seen: list[str] = []
    for effect in chain:
        for name in effect.required:
            if name not in seen:
                seen.append(name)
    return seen


def to_spec(chain: list[Effect], instruments: list[str], desc: str) -> dict:
    """Serialise a chain for the visualizer (written to ``logs/fx.json``)."""
    return {
        "desc": desc,
        "instruments": list(instruments),
        "effects": [
            {"name": e.name, "params": dict(e.params), "required": list(e.required)}
            for e in chain
        ],
    }


def from_spec(spec: dict) -> list[Effect]:
    """Rebuild a chain from :func:`to_spec` output (used inside the visualizer)."""
    chain: list[Effect] = []
    for entry in spec.get("effects", []):
        name = entry["name"]
        if name not in EFFECTS:
            raise SystemExit(f"unknown effect '{name}' in the FX spec")
        effect = EFFECTS[name](entry.get("params"))
        effect.required = tuple(entry.get("required", ()))
        chain.append(effect)
    return chain


def uses_strip(chain: list[Effect]) -> bool:
    """True if any shader effect in the chain reads the audio data strip."""
    return any(e.tier == "shader" and e.uses_strip for e in chain)


def paint_effects(chain: list[Effect]) -> list[Effect]:
    """The paint-tier effects of *chain*, in order."""
    return [e for e in chain if e.tier == "paint"]


# ---------------------------------------------------------------------------
# Shader assembly
# ---------------------------------------------------------------------------
# {name} braces are substituted with str.replace (GLSL contains real braces).
SHADER_BASE = """//!HOOK MAIN
//!BIND HOOKED
//!DESC {DESC}

#define FPS 30.0
{STRIP_HELPERS}{HELPERS}vec4 hook(){
{STRIP_MASK}    float t = float(frame)/FPS;
    float kick = {KICK};
    vec2 res = target_size;
    vec2 uv = (HOOKED_pos*res - 0.5*res)/res.y;
    float r = length(uv);

    vec3 col = HOOKED_tex(HOOKED_pos).rgb;
{APPLY}    return vec4(col, 1.0);
}
"""

_STRIP_HELPERS = (
    "// The audio data strip lives in the top rows of HOOKED (64 values across\n"
    "// the width); sample it in normalised coordinates.\n"
    "float strip(float idx){ return HOOKED_tex(vec2((idx+0.5)/64.0, 2.0/{H})).x; }\n"
    "float band(float b){ return strip(b); }\n"
    "float aux(float i){ return strip(64.0+i); }\n"
)
_STRIP_MASK = (
    "    // The top rows of HOOKED hold the audio data strip, not picture - hide it.\n"
    "    if (HOOKED_pos.y < 9.0/{H}) return vec4(0.0, 0.0, 0.0, 1.0);\n"
)


def assemble_shader(chain: list[Effect], desc: str, height: int = 1080) -> str:
    """Build the full GLSL shader for *chain* at a video *height*.

    Shader-tier effects contribute helper functions (before ``hook``) and apply
    statements (inside ``hook``), in chain order. The strip accessors and the
    strip mask only appear when an effect actually reads the strip, so a
    strip-less chain does not blank the picture's top rows. The strip row
    coordinates depend on the frame height (the strip is written into the top rows
    of a clip half the output size, so row 1 of the strip is at ``2/H``).
    """
    shaders = [e for e in chain if e.tier == "shader"]
    strip = any(e.uses_strip for e in shaders)
    helpers = "\n".join(h for h in (e.glsl_helpers() for e in shaders) if h)
    apply = "\n".join(a for a in (e.glsl_apply() for e in shaders) if a)
    rows = f"{float(height):.1f}"  # 1080.0 - keeps the default shader text identical
    return (
        SHADER_BASE.replace("{DESC}", desc)
        .replace(
            "{STRIP_HELPERS}",
            _STRIP_HELPERS.replace("{H}", rows) + "\n" if strip else "",
        )
        .replace("{HELPERS}", helpers + "\n\n" if helpers else ("\n" if strip else ""))
        .replace("{STRIP_MASK}", _STRIP_MASK.replace("{H}", rows) if strip else "")
        .replace("{KICK}", "aux(1.0)" if strip else "0.0")
        .replace("{APPLY}", apply + "\n" if apply else "")
    )
