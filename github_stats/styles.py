"""Activity card designs.

Five genuinely different renderings of the same year of contribution data, all
sharing one canvas size (880×250) so they are drop-in interchangeable in a README:

    aurora   gradient area + line, the line draws itself
    bars     one column per week, growing from the baseline
    blocks   the year as a 53×7 grid of tiles, fading in by column
    dial     monthly spokes around a dial, with the headline numbers beside it
    spark    nothing but the shape — the trend, no chrome

Each takes the resolved palette, so any design works in any palette and both
themes. Each animation is one-shot and settles: an embed is read, not watched.
"""

from __future__ import annotations

import html
import math

from github_stats.config import MONO, MONTHS, SANS

WIDTH, HEIGHT = 880, 250
DEFAULT_STYLE = "aurora"

# label, one-line description — surfaced in the web UI
STYLE_INFO = {
    "aurora": ("Aurora", "gradient area and line; the line draws itself"),
    "bars": ("Bars", "one column per week, rising from the baseline"),
    "blocks": ("Blocks", "the year as a 53×7 tile grid, revealed by column"),
    "dial": ("Dial", "monthly spokes around a dial, headline numbers beside it"),
    "spark": ("Spark", "just the shape — no grid, no axes"),
}
STYLE_NAMES = tuple(STYLE_INFO)


def is_style(name: str) -> bool:
    return name in STYLE_INFO


# ---------------------------------------------------------------------------
# shared geometry
# ---------------------------------------------------------------------------

LEFT, RIGHT, TOP, BOTTOM = 58, 28, 70, 48
INNER_W, INNER_H = WIDTH - LEFT - RIGHT, HEIGHT - TOP - BOTTOM


def _series(weeks: list[tuple[str, int]]) -> list[int]:
    return [total for _, total in weeks]


def _axis(totals: list[int]) -> tuple[int, int]:
    """(peak, axis max) — the top is rounded up to the next ten, and never zero."""
    peak = max(totals) if totals else 0
    top = max(10, -(-int(peak * 1.12) // 10) * 10) if peak else 10
    return peak, top


def _month_marks(weeks: list[tuple[str, int]]) -> list[tuple[int, str]]:
    marks: list[tuple[int, str]] = []
    seen: set[str] = set()
    for index, (date, _) in enumerate(weeks):
        month = date[:7]
        if month not in seen:
            seen.add(month)
            marks.append((index, month))
    if len(marks) > 1 and marks[0][1][5:] == marks[-1][1][5:]:
        marks.pop()                                   # trailing partial month
    return marks


def _monthly(weeks: list[tuple[str, int]]) -> list[tuple[str, int]]:
    """Weekly totals folded into months, oldest first."""
    buckets: dict[str, int] = {}
    for date, total in weeks:
        buckets[date[:7]] = buckets.get(date[:7], 0) + total
    items = list(buckets.items())
    if len(items) > 12:
        items = items[1:]                             # drop a partial leading month
    return items[-12:]


def _polyline_length(points: list[tuple[float, float]]) -> float:
    return sum(math.dist(points[i], points[i + 1]) for i in range(len(points) - 1))


def _plot(totals: list[int]):
    """Points inside the plot box plus the axis maths both charts need."""
    peak, axis_max = _axis(totals)
    scale = INNER_H / axis_max
    step = INNER_W / max(1, len(totals) - 1)
    points = [(LEFT + index * step, TOP + INNER_H - value * scale)
              for index, value in enumerate(totals)]
    return peak, axis_max, scale, step, points


def _grid(p: dict, axis_max: int) -> str:
    lines = "".join(
        f'<line x1="{LEFT}" y1="{TOP + INNER_H * i / 4:.0f}"'
        f' x2="{LEFT + INNER_W}" y2="{TOP + INNER_H * i / 4:.0f}"'
        f' stroke="{p["grid"]}" stroke-width="1"/>' for i in range(5))
    return lines + (
        f'<text x="{LEFT - 12}" y="{TOP + 4}" text-anchor="end" font-family="{MONO}"'
        f' font-size="10" fill="{p["dim"]}">{axis_max}</text>'
        f'<text x="{LEFT - 12}" y="{TOP + INNER_H + 4}" text-anchor="end"'
        f' font-family="{MONO}" font-size="10" fill="{p["dim"]}">0</text>')


def _title(p: dict, text: str) -> str:
    return (f'<text x="{LEFT}" y="42" font-family="{MONO}" font-size="11"'
            f' letter-spacing="2.4" fill="{p["dim"]}">{text}</text>')


def _chrome(p: dict) -> str:
    return (f'<rect width="{WIDTH}" height="{HEIGHT}" rx="12" fill="{p["bg"]}"'
            f' stroke="{p["border"]}"/>')


def _defs(p: dict, extra: str = "") -> str:
    return f'''<defs>
<linearGradient id="line" x1="0" y1="0" x2="1" y2="0">
<stop offset="0" stop-color="{p['a3']}"/><stop offset=".5" stop-color="{p['a2']}"/>
<stop offset="1" stop-color="{p['a1']}"/></linearGradient>
<linearGradient id="fill" x1="0" y1="0" x2="0" y2="1">
<stop offset="0" stop-color="{p['a2']}" stop-opacity=".42"/>
<stop offset="1" stop-color="{p['a1']}" stop-opacity="0"/></linearGradient>
<linearGradient id="bar" x1="0" y1="1" x2="0" y2="0">
<stop offset="0" stop-color="{p['a2']}" stop-opacity=".85"/>
<stop offset="1" stop-color="{p['a1']}"/></linearGradient>
<linearGradient id="ink" x1="0" y1="0" x2="1" y2="0">
<stop offset="0" stop-color="{p['a1']}"/><stop offset=".6" stop-color="{p['a2']}"/>
<stop offset="1" stop-color="{p['a3']}"/></linearGradient>
{extra}</defs>'''


def _svg(inner: str, desc: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}"'
            f' width="{WIDTH}" height="{HEIGHT}" role="img" aria-labelledby="at ad">'
            f'<title id="at">Contribution activity</title>'
            f'<desc id="ad">{html.escape(desc)}</desc>{inner}</svg>\n')


# ---------------------------------------------------------------------------
# aurora — area + line
# ---------------------------------------------------------------------------


def aurora(p: dict, user: str, weeks: list, days: list, motion: bool) -> str:
    totals = _series(weeks)
    peak, axis_max, scale, step, points = _plot(totals)
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    area = ("M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in points)
            + f" L{LEFT + INNER_W:.1f} {TOP + INNER_H} L{LEFT} {TOP + INNER_H} Z")
    length = _polyline_length(points)

    # The halo keeps the line legible where it rides the top of its own fill, and
    # stroke-dashoffset="0" is the settled value: a viewer that ignores SMIL still
    # gets a complete line rather than a half-drawn one.
    halo = (f'<polyline points="{line}" fill="none" stroke="{p["bg"]}"'
            f' stroke-width="5.5" stroke-linejoin="round" stroke-linecap="round"'
            f' opacity=".55"/>')
    draw = (f'<polyline points="{line}" fill="none" stroke="url(#line)"'
            f' stroke-width="2.6" stroke-linejoin="round" stroke-linecap="round"'
            f' stroke-dasharray="{length:.0f}" stroke-dashoffset="0">'
            f'<animate attributeName="stroke-dashoffset" from="{length:.0f}" to="0"'
            f' dur="1.15s" fill="freeze"/></polyline>') if motion else (
        f'<polyline points="{line}" fill="none" stroke="url(#line)"'
        f' stroke-width="2.6" stroke-linejoin="round" stroke-linecap="round"/>')

    marker = ""
    if peak:
        px, py = points[totals.index(peak)]
        marker = (f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4" fill="{p["a1"]}"/>'
                  f'<text x="{px - 10:.0f}" y="{py - 12:.0f}" text-anchor="end"'
                  f' font-family="{MONO}" font-size="10" fill="{p["ink"]}"'
                  f' letter-spacing="1">peak {peak}/week</text>')

    fade = '<animate attributeName="opacity" from="0" to="1" begin="0.55s" dur="0.7s" fill="freeze"/>' \
        if motion else ""
    labels = "".join(
        f'<text x="{LEFT + index * step:.0f}" y="{HEIGHT - 18}" font-family="{MONO}"'
        f' font-size="10" fill="{p["dim"]}" letter-spacing="1">'
        f'{MONTHS[int(month[5:7]) - 1]}</text>' for index, month in _month_marks(weeks))

    return _svg(
        _defs(p) + _chrome(p) + _grid(p, axis_max)
        + f'<path d="{area}" fill="url(#fill)">{fade}</path>'
        + halo + draw + marker
        + f'<line x1="{LEFT}" y1="{TOP + INNER_H}" x2="{LEFT + INNER_W}"'
          f' y2="{TOP + INNER_H}" stroke="{p["border"]}" stroke-width="1"/>'
        + labels
        + _title(p, "ACTIVITY &#183; WEEKLY TOTALS, LAST 12 MONTHS"),
        f"Weekly contribution totals for the last 12 months; peak week {peak}.")


# ---------------------------------------------------------------------------
# bars — one column per week
# ---------------------------------------------------------------------------


def bars(p: dict, user: str, weeks: list, days: list, motion: bool) -> str:
    totals = _series(weeks)
    peak, axis_max, scale, step, _ = _plot(totals)
    baseline = TOP + INNER_H
    bar_w = max(2.0, step * 0.62)

    bars_svg = []
    for index, value in enumerate(totals):
        height = value * scale
        x = LEFT + index * step - bar_w / 2
        y = baseline - height
        if value <= 0:
            bars_svg.append(
                f'<rect x="{x:.1f}" y="{baseline - 1.5:.1f}" width="{bar_w:.1f}"'
                f' height="1.5" rx=".75" fill="{p["grid"]}"/>')
            continue
        animate = (f'<animate attributeName="height" from="0" to="{height:.1f}"'
                   f' begin="{index * 0.010:.3f}s" dur="0.45s" fill="freeze"/>'
                   f'<animate attributeName="y" from="{baseline:.1f}" to="{y:.1f}"'
                   f' begin="{index * 0.010:.3f}s" dur="0.45s" fill="freeze"/>') if motion else ""
        bars_svg.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{height:.1f}"'
            f' rx="{min(3.0, bar_w / 2):.1f}" fill="url(#bar)">{animate}</rect>')

    marker = ""
    if peak:
        index = totals.index(peak)
        px = LEFT + index * step
        marker = (f'<text x="{px:.0f}" y="{baseline - peak * scale - 10:.0f}"'
                  f' text-anchor="middle" font-family="{MONO}" font-size="10"'
                  f' fill="{p["ink"]}" letter-spacing="1">peak {peak}/week</text>')
    labels = "".join(
        f'<text x="{LEFT + index * step:.0f}" y="{HEIGHT - 18}" font-family="{MONO}"'
        f' font-size="10" fill="{p["dim"]}" letter-spacing="1">'
        f'{MONTHS[int(month[5:7]) - 1]}</text>' for index, month in _month_marks(weeks))

    return _svg(
        _defs(p) + _chrome(p) + _grid(p, axis_max) + marker + "".join(bars_svg)
        + f'<line x1="{LEFT}" y1="{baseline}" x2="{LEFT + INNER_W}" y2="{baseline}"'
          f' stroke="{p["border"]}" stroke-width="1"/>'
        + labels
        + _title(p, "ACTIVITY &#183; ONE COLUMN PER WEEK"),
        f"Weekly contribution totals as columns; peak week {peak}.")


# ---------------------------------------------------------------------------
# blocks — the year as a tile grid
# ---------------------------------------------------------------------------


def blocks(p: dict, user: str, weeks: list, days: list, motion: bool) -> str:
    totals = _series(weeks)
    peak = max(totals) if totals else 0
    columns = max((day["week"] for day in days), default=len(weeks) - 1) + 1

    cell, gap, step = 12.0, 4.0, 16.0
    grid_w = columns * step - gap
    x0 = (WIDTH - grid_w) / 2
    y0 = 78.0

    ramp = list(p["levels"])
    cuts = sorted({max(1, math.ceil((peak or 1) * fraction))
                   for fraction in (.15, .35, .60, .85)})

    buckets: dict[int, list[dict]] = {}
    for day in days:
        buckets.setdefault(day["week"], []).append(day)

    cells = []
    for week_index, week in sorted(buckets.items()):
        for day in week:
            count = day["contributionCount"]
            level = 0
            for step_index, cut in enumerate(cuts):
                if count >= cut:
                    level = step_index + 1
            x = x0 + week_index * step
            y = y0 + day["dow"] * step
            animate = (f'<animate attributeName="opacity" from="0" to="1"'
                       f' begin="{min(0.9, week_index * 0.011 + day["dow"] * 0.004):.3f}s"'
                       f' dur="0.35s" fill="freeze"/>') if motion else ""
            cells.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell}" height="{cell}"'
                         f' rx="2.6" fill="{ramp[level]}">{animate}</rect>')

    marks = _month_marks(weeks) or []
    labels = "".join(
        f'<text x="{x0 + index * step:.0f}" y="{y0 + 7 * step + 4:.0f}"'
        f' font-family="{MONO}" font-size="10" fill="{p["dim"]}" letter-spacing="1">'
        f'{MONTHS[int(month[5:7]) - 1]}</text>' for index, month in marks)

    legend_y = HEIGHT - 34
    legend = (f'<text x="{LEFT}" y="{legend_y + 11}" font-family="{MONO}" font-size="10"'
              f' letter-spacing="1.6" fill="{p["dim"]}">LESS</text>')
    for index in range(5):
        legend += (f'<rect x="{LEFT + 44 + index * 18:.0f}" y="{legend_y}" width="13"'
                   f' height="13" rx="3" fill="{ramp[index]}"/>')
    legend += (f'<text x="{LEFT + 44 + 5 * 18 + 6:.0f}" y="{legend_y + 11}"'
               f' font-family="{MONO}" font-size="10" letter-spacing="1.6"'
               f' fill="{p["dim"]}">MORE</text>')
    summary = (f'<text x="{WIDTH - RIGHT}" y="{legend_y + 11}" text-anchor="end"'
               f' font-family="{MONO}" font-size="10" letter-spacing="1.6"'
               f' fill="{p["dim"]}">PEAK {peak}/WEEK</text>')

    return _svg(
        _defs(p) + _chrome(p) + "".join(cells) + labels + legend + summary
        + _title(p, "ACTIVITY &#183; EVERY DAY, LAST 12 MONTHS"),
        f"Every day of the last 12 months as a tile; peak week {peak}.")


# ---------------------------------------------------------------------------
# dial — monthly spokes
# ---------------------------------------------------------------------------


def dial(p: dict, user: str, weeks: list, days: list, motion: bool) -> str:
    months = _monthly(weeks)
    values = [total for _, total in months]
    best = max(values) if values else 0
    best_month = months[values.index(best)][0] if best else (months[0][0] if months else "2026-01")
    peak, _axis_max = _axis(_series(weeks))

    cx, cy, inner, outer = 250.0, 140.0, 44.0, 86.0
    span = outer - inner
    ramp = list(p["levels"][1:])

    guides = "".join(
        f'<circle cx="{cx}" cy="{cy}" r="{inner + span * (i / 3):.1f}" fill="none"'
        f' stroke="{p["grid"]}" stroke-width="1"/>' for i in range(4))

    # Month names live only in the summary block; around the dial they collided
    # with the card edge. The dial carries the shape, the numbers carry the detail.
    best_index = values.index(best) if best else -1
    spokes = []
    for index, (month, total) in enumerate(months):
        angle = math.radians(-90 + index * 30)
        reach = (total / best * span) if best else 0
        level = 0 if not total else min(4, max(1, math.ceil(total / (best or 1) * 4)))
        colour = ramp[level - 1] if level else p["grid"]
        width = 14 if index == best_index else 11
        x1, y1 = cx + math.cos(angle) * inner, cy + math.sin(angle) * inner
        x2 = cx + math.cos(angle) * (inner + max(reach, 3))
        y2 = cy + math.sin(angle) * (inner + max(reach, 3))
        spoke = (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"'
                 f' stroke="{colour}" stroke-width="{width}" stroke-linecap="round"')
        # No base opacity attribute: the fade exists only inside the animation, so
        # a viewer that ignores SMIL still draws every spoke.
        if motion:
            spoke += (f'><animate attributeName="opacity" from="0" to="1"'
                      f' begin="{0.08 + index * 0.045:.3f}s" dur="0.4s"'
                      f' fill="freeze"/></line>')
        else:
            spoke += "/>"
        spokes.append(spoke)

    first_month = months[0][0] if months else "2026-01"
    last_month = months[-1][0] if months else first_month
    centre = (f'<text x="{cx:.0f}" y="{cy + 4:.0f}" text-anchor="middle"'
              f' font-family="{MONO}" font-size="9.5" letter-spacing="1.6"'
              f' fill="{p["dim"]}">{MONTHS[int(first_month[5:7]) - 1].upper()}'
              f'&#8211;{MONTHS[int(last_month[5:7]) - 1].upper()}</text>')

    total = sum(_series(weeks))   # the true period total: the spokes are only a
    # breakdown of it, so trimming a partial leading month must not change the number.
    right = (f'<text x="416" y="118" font-family="{SANS}" font-size="46"'
             f' font-weight="800" fill="url(#ink)">{total}</text>'
             f'<text x="{416 + len(str(total)) * 30 + 14}" y="118"'
             f' font-family="{MONO}" font-size="13" letter-spacing="2.5"'
             f' fill="{p["dim"]}">CONTRIBUTIONS</text>'
             f'<text x="416" y="166" font-family="{MONO}" font-size="11"'
             f' letter-spacing="1.4" fill="{p["dim"]}">BEST MONTH'
             f'  <tspan fill="{p["ink"]}">{MONTHS[int(best_month[5:7]) - 1]}'
             f' &#183; {best}</tspan></text>'
             f'<text x="416" y="192" font-family="{MONO}" font-size="11"'
             f' letter-spacing="1.4" fill="{p["dim"]}">PEAK WEEK'
             f'  <tspan fill="{p["ink"]}">{peak}</tspan></text>'
             f'<text x="416" y="218" font-family="{MONO}" font-size="11"'
             f' letter-spacing="1.4" fill="{p["dim"]}">MONTHS SHOWN'
             f'  <tspan fill="{p["ink"]}">{len(months)}</tspan></text>')

    spin = (f'<animateTransform attributeName="transform" type="rotate"'
            f' from="-14 {cx} {cy}" to="0 {cx} {cy}" dur="1s" fill="freeze"/>') if motion else ""
    return _svg(
        _defs(p) + _chrome(p)
        + f'<g>{spin}{guides}{"".join(spokes)}{centre}</g>'
        + right + _title(p, "ACTIVITY &#183; LAST 12 MONTHS"),
        f"Monthly contribution spokes; best month {best_month} with {best}.")


# ---------------------------------------------------------------------------
# spark — the shape, nothing else
# ---------------------------------------------------------------------------


def spark(p: dict, user: str, weeks: list, days: list, motion: bool) -> str:
    totals = _series(weeks)
    peak, _axis_max = _axis(totals)
    scale = 118.0 / (peak or 1)
    step = (WIDTH - 120) / max(1, len(totals) - 1)
    points = [(60 + index * step, 214 - value * scale)
              for index, value in enumerate(totals)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    area = ("M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in points)
            + f" L{WIDTH - 60:.1f} 224 L60 224 Z")
    length = _polyline_length(points)

    halo = (f'<polyline points="{line}" fill="none" stroke="{p["bg"]}"'
            f' stroke-width="6" stroke-linejoin="round" stroke-linecap="round"'
            f' opacity=".55"/>')
    draw = (f'<polyline points="{line}" fill="none" stroke="url(#line)"'
            f' stroke-width="3" stroke-linejoin="round" stroke-linecap="round"'
            f' stroke-dasharray="{length:.0f}" stroke-dashoffset="0">'
            f'<animate attributeName="stroke-dashoffset" from="{length:.0f}" to="0"'
            f' dur="1.2s" fill="freeze"/></polyline>') if motion else (
        f'<polyline points="{line}" fill="none" stroke="url(#line)"'
        f' stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>')

    fade = ('<animate attributeName="opacity" from="0" to="1" begin="0.6s"'
            ' dur="0.6s" fill="freeze"/>') if motion else ""
    total = sum(totals)
    return _svg(
        _defs(p) + _chrome(p)
        + f'<text x="60" y="96" font-family="{SANS}" font-size="46" font-weight="800"'
          f' fill="url(#line)">{total}</text>'
        + f'<text x="{60 + len(str(total)) * 30 + 14}" y="96" font-family="{MONO}"'
          f' font-size="13" letter-spacing="2.5" fill="{p["dim"]}">CONTRIBUTIONS</text>'
        + f'<text x="{WIDTH - 60}" y="96" text-anchor="end" font-family="{MONO}"'
          f' font-size="11" letter-spacing="1.6" fill="{p["dim"]}">PEAK {peak}/WEEK</text>'
        + f'<path d="{area}" fill="url(#fill)">{fade}</path>'
        + halo + draw
        + f'<line x1="60" y1="224" x2="{WIDTH - 60}" y2="224"'
          f' stroke="{p["border"]}" stroke-width="1"/>'
        + _title(p, "ACTIVITY &#183; LAST 12 MONTHS"),
        f"Contribution trend for the last 12 months; peak week {peak}.")


RENDERERS = {"aurora": aurora, "bars": bars, "blocks": blocks, "dial": dial, "spark": spark}


def render(style: str, palette: dict, user: str, weeks: list, days: list,
           motion: bool) -> str:
    """Dispatch to one design; unknown names fall back to the default."""
    return RENDERERS.get(style, aurora)(palette, user, weeks, days, motion)
