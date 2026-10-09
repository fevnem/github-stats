"""The two flat stat cards: streak totals and weekly activity."""

from __future__ import annotations

import html

from github_stats.config import MONO, MONTHS, SANS

STREAK_W, STREAK_H = 520, 200
ACTIVITY_W, ACTIVITY_H = 880, 250


def streak_card(palette: dict, user: str, total: int, current: int,
                longest: int) -> str:
    """Totals on the left, current streak in the middle, longest on the right."""
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


def activity_card(palette: dict, user: str, weeks: list[tuple[str, int]]) -> str:
    """Weekly totals as a filled line chart with a rounded, honest y-axis."""
    width, height = ACTIVITY_W, ACTIVITY_H
    left, right, top, bottom = 58, 28, 70, 48
    inner_w, inner_h = width - left - right, height - top - bottom

    totals = [total for _, total in weeks]
    peak = max(totals) if totals else 0
    # An honest axis: rounded up to the next ten, never zero-height.
    axis_max = max(10, -(-int(peak * 1.12) // 10) * 10) if peak else 10
    scale = inner_h / axis_max
    step = inner_w / max(1, len(totals) - 1)
    points = [(left + index * step, top + inner_h - value * scale)
              for index, value in enumerate(totals)]

    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    area = ("M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in points)
            + f" L{left + inner_w:.1f} {top + inner_h} L{left} {top + inner_h} Z")

    grid = "".join(
        f'<line x1="{left}" y1="{top + inner_h * i / 4:.0f}"'
        f' x2="{left + inner_w}" y2="{top + inner_h * i / 4:.0f}"'
        f' stroke="{palette["grid"]}" stroke-width="1"/>' for i in range(5))
    grid += (f'<text x="{left - 12}" y="{top + 4}" text-anchor="end"'
             f' font-family="{MONO}" font-size="10" fill="{palette["dim"]}">{axis_max}</text>'
             f'<text x="{left - 12}" y="{top + inner_h + 4}" text-anchor="end"'
             f' font-family="{MONO}" font-size="10" fill="{palette["dim"]}">0</text>')

    marks: list[tuple[int, str]] = []
    seen: set[str] = set()
    for index, (date, _) in enumerate(weeks):
        month = date[:7]
        if month not in seen:
            seen.add(month)
            marks.append((index, month))
    if len(marks) > 1 and marks[0][1][5:] == marks[-1][1][5:]:
        marks.pop()                                   # trailing partial month
    labels = [f'<text x="{left + index * step:.0f}" y="{height - 18}"'
              f' font-family="{MONO}" font-size="10" fill="{palette["dim"]}"'
              f' letter-spacing="1">{MONTHS[int(month[5:7]) - 1]}</text>'
              for index, month in marks]

    marker = ""
    if peak:                                 # a quiet year has no peak to point at
        peak_x, peak_y = points[totals.index(peak)]
        marker = (f'<circle cx="{peak_x:.1f}" cy="{peak_y:.1f}" r="4"'
                  f' fill="{palette["a1"]}"/>'
                  f'<text x="{peak_x - 10:.0f}" y="{peak_y - 12:.0f}" text-anchor="end"'
                  f' font-family="{MONO}" font-size="10" fill="{palette["ink"]}"'
                  f' letter-spacing="1">peak {peak}/week</text>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img" aria-labelledby="at ad">
<title id="at">Contribution activity</title>
<desc id="ad">Weekly contribution totals for the last 12 months; peak week {peak}.</desc>
<defs>
<linearGradient id="af" x1="0" y1="0" x2="0" y2="1">
<stop offset="0" stop-color="{palette['a2']}" stop-opacity=".55"/>
<stop offset="1" stop-color="{palette['a1']}" stop-opacity="0"/></linearGradient>
<linearGradient id="al" x1="0" y1="0" x2="1" y2="0">
<stop offset="0" stop-color="{palette['a3']}"/><stop offset="1" stop-color="{palette['a1']}"/></linearGradient>
</defs>
<rect width="{width}" height="{height}" rx="12" fill="{palette['bg']}" stroke="{palette['border']}"/>
{grid}
<path d="{area}" fill="url(#af)"/>
<polyline points="{line}" fill="none" stroke="url(#al)" stroke-width="2.4" stroke-linejoin="round"/>
{marker}
<line x1="{left}" y1="{top + inner_h}" x2="{left + inner_w}" y2="{top + inner_h}" stroke="{palette['border']}" stroke-width="1"/>
{"".join(labels)}
<text x="{left}" y="42" font-family="{MONO}" font-size="11" letter-spacing="2.4" fill="{palette['dim']}">ACTIVITY &#183; WEEKLY TOTALS, LAST 12 MONTHS</text>
</svg>
'''
