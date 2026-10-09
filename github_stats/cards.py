"""The streak card: totals, current streak, longest streak."""

from __future__ import annotations

import html

from github_stats.config import MONO, SANS

STREAK_W, STREAK_H = 520, 200


def streak_card(palette: dict, user: str, total: int, current: int,
                longest: int) -> str:
    """One row, three columns, one gradient across all three numerals."""
    width, height = STREAK_W, STREAK_H
    third = width / 3
    who = html.escape(user)
    columns = [(total, "TOTAL CONTRIBUTIONS"),
               (current, "CURRENT STREAK"),
               (longest, "LONGEST STREAK")]

    parts: list[str] = []
    for index, (value, label) in enumerate(columns):
        centre = third * (index + 0.5)
        parts.append(
            f'<text x="{centre:.0f}" y="112" text-anchor="middle"'
            f' font-family="{SANS}" font-size="42" font-weight="800"'
            f' fill="url(#sg)">{value}</text>'
            f'<text x="{centre:.0f}" y="141" text-anchor="middle"'
            f' font-family="{MONO}" font-size="9.5" letter-spacing="1.4"'
            f' fill="{palette["dim"]}">{label}</text>')
        if index:
            parts.append(
                f'<line x1="{third * index:.0f}" y1="72" x2="{third * index:.0f}"'
                f' y2="148" stroke="{palette["div"]}" stroke-width="1.2"/>')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img" aria-labelledby="st sd">
<title id="st">Contribution streak</title>
<desc id="sd">{total} contributions, current streak {current} days, longest streak {longest} days.</desc>
<defs>
<clipPath id="scard"><rect width="{width}" height="{height}" rx="12"/></clipPath>
<linearGradient id="sg" gradientUnits="userSpaceOnUse" x1="30" y1="0" x2="490" y2="0">
<stop offset="0" stop-color="{palette['a1']}"/><stop offset=".55" stop-color="{palette['a2']}"/>
<stop offset="1" stop-color="{palette['a3']}"/></linearGradient>
<linearGradient id="sh" x1="0" y1="0" x2="1" y2="0">
<stop offset="0" stop-color="{palette['a1']}" stop-opacity="0"/>
<stop offset=".45" stop-color="{palette['a1']}" stop-opacity=".95"/>
<stop offset="1" stop-color="{palette['a3']}" stop-opacity="0"/></linearGradient>
</defs>
<rect width="{width}" height="{height}" rx="12" fill="{palette['bg']}" stroke="{palette['border']}"/>
<g clip-path="url(#scard)"><rect x="0" y="0" width="{width}" height="4" fill="url(#sh)"/></g>
<text x="{width / 2:.0f}" y="44" text-anchor="middle" font-family="{MONO}" font-size="10.5" letter-spacing="2" fill="{palette['dim']}">CONTRIBUTION STREAK</text>
{"".join(parts)}
<text x="24" y="{height - 20}" font-family="{MONO}" font-size="10" letter-spacing="2.4" fill="{palette['dim']}">LIVE</text>
<text x="{width - 24}" y="{height - 20}" text-anchor="end" font-family="{MONO}" font-size="10" letter-spacing="1.6" fill="{palette['dim']}">github.com/{who}</text>
</svg>
'''
