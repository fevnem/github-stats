"""Static configuration: palettes, geometry metrics and cache policy."""

from __future__ import annotations

VERSION = "1.1.0"

# Upstream reads are bounded so a slow GitHub never holds a profile render.
HTTP_TIMEOUT = 15
USER_AGENT = "github-stats/" + VERSION

# Served from the CDN for 10 minutes, then revalidated in the background: fresh
# enough to call live, polite enough that a profile view never hammers GitHub.
CACHE_HEADERS = [
    ("Cache-Control", "public, max-age=300, s-maxage=600, stale-while-revalidate=900"),
]
ERROR_CACHE_HEADERS = [("Cache-Control", "public, max-age=60")]

MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
SANS = "'Segoe UI',system-ui,-apple-system,'Helvetica Neue',Arial,sans-serif"

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

CARD_THEMES = {
    "dark": dict(bg="#0d0b14", border="#2f1a47", div="#42306e", ink="#ffffff",
                 dim="#a08cc9", a1="#FF00F6", a2="#7C3AED", a3="#22D3EE",
                 grid="#241a3d"),
    "light": dict(bg="#ffffff", border="#e3dcf7", div="#d6cbf2", ink="#160e2c",
                  dim="#6f5f9c", a1="#d600d0", a2="#6d28d9", a3="#0891b2",
                  grid="#ece7fa"),
}

FIELD_THEMES = {
    "dark": dict(bg0="#0a0710", bg1="#150e26", grid="#2a1c4d", ink="#efe9ff",
                 dim="#b9a5ea", tick="#e2d7ff", empty="#241b46", empty_top="#2e2358",
                 plane="#0f0a1e", plane_edge="#4a3778",
                 scale=[("#4a2586", "#341a5f"), ("#7c3aed", "#5b21b6"),
                        ("#b41fbb", "#8b158f"), ("#FF00F6", "#c026d3")],
                 total="#FF00F6"),
    "light": dict(bg0="#ffffff", bg1="#f5f2ff", grid="#e6dff8", ink="#1a1030",
                  dim="#6b5a99", tick="#412f70", empty="#e6dff8", empty_top="#efebfb",
                  plane="#f7f4ff", plane_edge="#b9a8e6",
                  scale=[("#7c3aed", "#a78bfa"), ("#a21caf", "#c026d3"),
                         ("#d600d0", "#e879f9"), ("#c200c2", "#f0abfc")],
                  total="#a21caf"),
}

# Field geometry, in SVG user units.
FIELD_W, FIELD_H = 900, 400
FIELD_OX, FIELD_OY = 190.0, 126.0     # far corner of the base plane
FIELD_TW, FIELD_TH = 20.0, 10.0       # isometric tile width / height (2:1)
FIELD_Z = 3.05                        # pixels of height per contribution
FIELD_DAYS, FIELD_WEEKS = 7, 53

KINDS = ("streak", "activity", "field")
