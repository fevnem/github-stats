"""Colour.

Two orthogonal axes, so a card can be customised without touching its geometry:

- **mode**   — `dark` or `light`: the surface the card is drawn on. Follows the
  reader's OS setting through a `<picture>` element.
- **palette** — the accent set: the gradient, the highlights, the field ramp.

Everything else (borders, grids, muted text, the 3-D field's tile ramp) is derived
from those two, so adding a palette is a three-colour change rather than a dozen.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# colour maths
# ---------------------------------------------------------------------------


def _rgb(colour: str) -> tuple[int, int, int]:
    colour = colour.lstrip("#")
    return tuple(int(colour[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def _hex(rgb: tuple[float, float, float]) -> str:
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(channel))) for channel in rgb)


def shade(colour: str, factor: float) -> str:
    """Darken (factor < 1) or lighten (factor > 1) towards black/white."""
    return _hex(tuple(channel * factor for channel in _rgb(colour)))


def mix(first: str, second: str, amount: float) -> str:
    """Blend `amount` of `second` into `first` (0.0–1.0)."""
    a, b = _rgb(first), _rgb(second)
    return _hex(tuple(a[i] + (b[i] - a[i]) * amount for i in range(3)))


# ---------------------------------------------------------------------------
# surfaces
# ---------------------------------------------------------------------------

BASE = {
    "dark": dict(
        bg="#0d0b14", bg0="#0a0710", bg1="#150e26", panel="#120c22",
        ink="#ffffff", dim="#a08cc9", border="#2f1a47", div="#42306e",
        grid="#241a3d",
    ),
    "light": dict(
        bg="#ffffff", bg0="#ffffff", bg1="#f5f2ff", panel="#ffffff",
        ink="#160e2c", dim="#6f5f9c", border="#e3dcf7", div="#d6cbf2",
        grid="#ece7fa",
    ),
}

# ---------------------------------------------------------------------------
# palettes: (a1, a2, a3) per mode — gradient start, gradient middle, gradient end
# ---------------------------------------------------------------------------

PALETTES: dict[str, dict] = {
    "aurora": dict(label="Aurora", blurb="magenta → violet → cyan",
                   dark=("#FF00F6", "#7C3AED", "#22D3EE"),
                   light=("#d600d0", "#6d28d9", "#0891b2")),
    "ember": dict(label="Ember", blurb="amber → rose → gold",
                  dark=("#FF8A00", "#FF3D71", "#FFD166"),
                  light=("#e8590c", "#d6336c", "#a16207")),
    "ice": dict(label="Ice", blurb="cyan → blue → frost",
                dark=("#22D3EE", "#3B82F6", "#A5F3FC"),
                light=("#0891b2", "#1d4ed8", "#0e7490")),
    "forest": dict(label="Forest", blurb="emerald → jade → lime",
                   dark=("#34D399", "#10B981", "#A3E635"),
                   light=("#047857", "#059669", "#4d7c0f")),
    "candy": dict(label="Candy", blurb="pink → lavender → sky",
                  dark=("#F472B6", "#A78BFA", "#38BDF8"),
                  light=("#db2777", "#7c3aed", "#0284c7")),
    "mono": dict(label="Mono", blurb="graphite → silver → white",
                 dark=("#9CA3AF", "#E5E7EB", "#FFFFFF"),
                 light=("#6b7280", "#111827", "#000000")),
}

DEFAULT_PALETTE = "aurora"
PALETTE_NAMES = tuple(PALETTES)


def is_palette(name: str) -> bool:
    return name in PALETTES


# ---------------------------------------------------------------------------
# resolution
# ---------------------------------------------------------------------------


def resolve(palette: str, mode: str) -> dict:
    """Everything a flat card needs, including the intensity ramp."""
    mode = "light" if mode == "light" else "dark"
    entry = PALETTES.get(palette) or PALETTES[DEFAULT_PALETTE]
    a1, a2, a3 = entry[mode]
    base = BASE[mode]
    dark = mode == "dark"

    # Four steps from "barely there" to the brightest accent: the charts that
    # colour by intensity (blocks, dial) walk this ramp.
    ramp = [
        mix(base["bg0"], a2, 0.45 if dark else 0.38),
        a2,
        mix(a2, a1, 0.50),
        a1,
    ]
    return dict(base, a1=a1, a2=a2, a3=a3, glow=a2, mode=mode,
                palette=palette, label=entry["label"], ramp=ramp,
                levels=[mix(base["bg0"], a2, 0.16 if dark else 0.13)] + ramp)


def resolve_field(palette: str, mode: str) -> dict:
    """`resolve` plus the tones only the isometric field needs — tile sides."""
    p = resolve(palette, mode)
    a1, a2, base = p["a1"], p["a2"], BASE[p["mode"]]
    dark = p["mode"] == "dark"
    p.update(
        plane=base["bg0"],
        plane_edge=mix(base["border"], a2, 0.40),
        empty=p["levels"][0],
        empty_top=mix(base["bg0"], a2, 0.18 if dark else 0.13),
        scale=[(top, shade(top, 0.66)) for top in p["ramp"]],
        total=a1,
        tick=base["ink"] if not dark else mix(base["ink"], a2, 0.12),
    )
    return p


def swatch(palette: str) -> dict:
    """Just enough for the UI to draw a palette chip client-side."""
    entry = PALETTES[palette]
    return dict(name=palette, label=entry["label"], blurb=entry["blurb"],
                dark=list(entry["dark"]), light=list(entry["light"]))
