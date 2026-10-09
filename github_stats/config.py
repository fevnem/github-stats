"""Static configuration: palettes, geometry metrics and cache policy."""

from __future__ import annotations

VERSION = "1.2.0"

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

# Palettes and their derived tones live in github_stats.palettes.

# Field geometry, in SVG user units.
FIELD_W, FIELD_H = 900, 400
FIELD_OX, FIELD_OY = 190.0, 126.0     # far corner of the base plane
FIELD_TW, FIELD_TH = 20.0, 10.0       # isometric tile width / height (2:1)
FIELD_MAX_H = 78.0                     # tallest column, in px — heights are
                                       # normalised to the year's busiest day
FIELD_DAYS, FIELD_WEEKS = 7, 53

KINDS = ("streak", "activity", "field")
