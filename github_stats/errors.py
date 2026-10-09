"""Failure output.

A README embed must never show a broken-image icon, so an error is drawn as a
card of the right size and returned with HTTP 200. Something always renders.
"""

from __future__ import annotations

import html

from github_stats.config import MONO

SIZES = {"streak": (520, 200), "activity": (880, 250), "field": (900, 400)}


def error_card(kind: str, palette: dict, message: str) -> str:
    """A drawable card carrying the reason, in the size the caller expected."""
    width, height = SIZES.get(kind, (520, 200))
    reason = html.escape(message[:70])
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img" aria-labelledby="et ed">
<title id="et">Stats unavailable</title>
<desc id="ed">{reason}</desc>
<rect width="{width}" height="{height}" rx="12" fill="{palette['bg']}" stroke="{palette['border']}"/>
<text x="{width / 2:.0f}" y="{height / 2 - 6:.0f}" text-anchor="middle" font-family="{MONO}" font-size="13" letter-spacing="2" fill="{palette['dim']}">STATS TEMPORARILY UNAVAILABLE</text>
<text x="{width / 2:.0f}" y="{height / 2 + 20:.0f}" text-anchor="middle" font-family="{MONO}" font-size="11" fill="{palette['ink']}">{reason}</text>
</svg>
'''
