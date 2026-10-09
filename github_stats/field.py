"""The isometric 3-D contribution field.

Each day of the last year is a tile on an isometric plane; its height and colour
encode that day's contribution count. Columns are drawn back-to-front so nearer
tiles overlap farther ones, which is what makes the plane read as solid.
"""

from __future__ import annotations

import html
import math

from github_stats.config import (FIELD_DAYS, FIELD_H, FIELD_MAX_H, FIELD_OX, FIELD_OY,
                                 FIELD_TW, FIELD_TH, FIELD_W, FIELD_WEEKS, MONTHS)

Point = tuple[float, float]

# Column heights are normalised, not linear in the raw count: a day with 400
# contributions and a day with 4 must both be visible on a 400px canvas, and a
# little compression reads as a landscape rather than a wall of spikes.
HEIGHT_CURVE = 0.65


def _iso(week: float, day: float, height: float = 0.0) -> Point:
    """Project grid coordinates onto the isometric plane."""
    return (FIELD_OX + (week + day) * (FIELD_TW / 2),
            FIELD_OY + (week - day) * (FIELD_TH / 2) - height)


def _shade(colour: str, factor: float) -> str:
    red, green, blue = (int(colour[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % (int(red * factor), int(green * factor), int(blue * factor))


def _level(count: int, cuts: list[int]) -> int:
    for index, cut in enumerate(cuts):
        if count >= cut:
            return index + 1
    return 0


def _column(week: int, day: int, count: int, peak: int, palette: dict, cuts: list[int]):
    """One tile: two side faces (only when it has height) and a top face."""
    height = FIELD_MAX_H * (count / peak) ** HEIGHT_CURVE if count else 0.0
    top = _iso(week, day, height)
    right = _iso(week + 1, day, height)
    front = _iso(week, day + 1, height)
    back = _iso(week + 1, day + 1, height)
    right_base = _iso(week + 1, day)
    front_base = _iso(week, day + 1)
    back_base = _iso(week + 1, day + 1)

    level = _level(count, cuts)
    if level == 0:
        top_fill, side = palette["empty_top"], palette["empty"]
    else:
        top_fill, side = palette["scale"][level - 1]
    side_dark = _shade(side, 0.74)

    faces = ""
    if count:
        faces += (f'<path d="M{right[0]:.1f} {right[1]:.1f} L{back[0]:.1f} {back[1]:.1f} '
                  f'L{back_base[0]:.1f} {back_base[1]:.1f} L{right_base[0]:.1f} {right_base[1]:.1f} Z"'
                  f' fill="{side}"/>'
                  f'<path d="M{front[0]:.1f} {front[1]:.1f} L{back[0]:.1f} {back[1]:.1f} '
                  f'L{back_base[0]:.1f} {back_base[1]:.1f} L{front_base[0]:.1f} {front_base[1]:.1f} Z"'
                  f' fill="{side_dark}"/>')
    faces += (f'<path d="M{top[0]:.1f} {top[1]:.1f} L{right[0]:.1f} {right[1]:.1f} '
              f'L{back[0]:.1f} {back[1]:.1f} L{front[0]:.1f} {front[1]:.1f} Z"'
              f' fill="{top_fill}"'
              + (f' stroke="{palette["plane_edge"]}" stroke-opacity="1" stroke-width="1"'
                 if level == 0 else "") + '/>')
    return (week - day, faces)                        # sort key: back to front


def field_svg(palette: dict, calendar: dict) -> str:
    """Draw the whole field for one resolved palette."""
    weeks = calendar["weeks"]
    days = [day for week in weeks for day in week["contributionDays"]]
    peak = max(day["contributionCount"] for day in days) or 1
    cuts = sorted({max(1, math.ceil(peak * fraction))
                   for fraction in (.10, .25, .48, .75)})

    columns = [
        _column(week_index, day_index, day["contributionCount"], peak, palette, cuts)
        for week_index, week in enumerate(weeks)
        for day_index, day in enumerate(week["contributionDays"])
    ]
    columns.sort(key=lambda column: column[0])        # back-to-front overlap

    corners = [_iso(0, 0), _iso(FIELD_WEEKS, 0), _iso(FIELD_WEEKS, FIELD_DAYS),
               _iso(0, FIELD_DAYS)]
    plane = ('<path d="' + " ".join(
        ("M" if index == 0 else "L") + f"{x:.1f} {y:.1f}"
        for index, (x, y) in enumerate(corners))
        + f' Z" fill="{palette["plane"]}" stroke="{palette["plane_edge"]}" stroke-width="1"/>')

    marks: list[tuple[int, str]] = []
    seen: set[str] = set()
    for week_index, week in enumerate(weeks):
        month = week["contributionDays"][0]["date"][:7]
        if month not in seen:
            seen.add(month)
            marks.append((week_index, month))
    if len(marks) > 1 and marks[0][1][5:] == marks[-1][1][5:]:
        marks.pop()                                   # trailing partial month
    ticks = []
    for week_index, month in marks:
        x, y = _iso(week_index, FIELD_DAYS + 0.05)
        ticks.append(f'<text x="{x - 4:.0f}" y="{y + 17:.0f}" font-size="14"'
                     f' font-family="ui-monospace,Menlo,monospace"'
                     f' fill="{palette["tick"]}" letter-spacing="1">'
                     f'{MONTHS[int(month[5:7]) - 1]}</text>')

    legend_x = corners[0][0] - 178
    legend = [f'<text x="{legend_x:.0f}" y="{FIELD_H - 68}" font-size="11"'
              f' font-family="ui-monospace,Menlo,monospace" fill="{palette["dim"]}"'
              f' letter-spacing="1.4">CONTRIBUTIONS PER DAY</text>'
              f'<text x="{legend_x:.0f}" y="{FIELD_H - 44}" font-size="11"'
              f' font-family="ui-monospace,Menlo,monospace" fill="{palette["dim"]}"'
              f' letter-spacing="1.4">LESS</text>']
    for index in range(5):
        fill = palette["empty_top"] if index == 0 else palette["scale"][index - 1][0]
        legend.append(f'<rect x="{legend_x + 44 + index * 19:.0f}" y="{FIELD_H - 56}"'
                      f' width="14" height="14" rx="3" fill="{fill}"'
                      f' stroke="{palette["plane_edge"]}" stroke-width=".7"/>')
    legend.append(f'<text x="{legend_x + 44 + 5 * 19 + 4:.0f}" y="{FIELD_H - 44}"'
                  f' font-size="11" font-family="ui-monospace,Menlo,monospace"'
                  f' fill="{palette["dim"]}" letter-spacing="1.4">MORE</text>')

    total = str(calendar["totalContributions"])
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {FIELD_W} {FIELD_H}" width="{FIELD_W}" height="{FIELD_H}" role="img" aria-labelledby="ct cd">
<title id="ct">Contribution calendar, 3-D</title>
<desc id="cd">{calendar['totalContributions']} contributions over the last 12 months, drawn as an isometric bar field.</desc>
<defs>
<linearGradient id="cbg" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="{palette['bg0']}"/><stop offset="1" stop-color="{palette['bg1']}"/></linearGradient>
<filter id="cglow" x="-12%" y="-12%" width="124%" height="128%">
  <feDropShadow dx="0" dy="10" stdDeviation="12" flood-color="{palette['glow']}" flood-opacity=".3"/></filter>
<linearGradient id="cscrim" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="{palette['bg0']}" stop-opacity=".96"/>
  <stop offset=".5" stop-color="{palette['bg0']}" stop-opacity=".72"/>
  <stop offset="1" stop-color="{palette['bg0']}" stop-opacity="0"/></linearGradient>
</defs>
<rect width="{FIELD_W}" height="{FIELD_H}" fill="url(#cbg)"/>
<g filter="url(#cglow)">{plane}{"".join(column[1] for column in columns)}</g>
<rect width="470" height="190" fill="url(#cscrim)"/>
{"".join(ticks)}
<text x="30" y="56" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" font-size="12" letter-spacing="3" fill="{palette['dim']}">CONTRIBUTION FIELD &#183; LAST 12 MONTHS</text>
<text x="30" y="118" font-family="'Segoe UI',system-ui,-apple-system,Arial,sans-serif" font-size="46" font-weight="800" fill="{palette['total']}">{html.escape(total)}</text>
<text x="{30 + len(total) * 30 + 14}" y="118" font-family="ui-monospace,Menlo,monospace" font-size="13" letter-spacing="2.5" fill="{palette['dim']}">CONTRIBUTIONS</text>
{"".join(legend)}
</svg>
'''
