#!/usr/bin/env python3
"""github-stats — live GitHub contribution stats, rendered as SVG.

A single dependency-free Vercel serverless function (stdlib only, no token
required). The public contribution calendar GitHub renders on every profile is
parsed directly, so a fresh deploy works with zero configuration and there is no
secret to leak. If GitHub ever changes that markup, an optional GH_TOKEN is used
to fall back to the GraphQL API.

Routes
    /streak?user=fevnem           totals, current streak, longest streak
    /activity?user=fevnem         weekly totals over the last 12 months
    /field?user=fevnem            the isometric 3-D contribution field
    /?user=fevnem                 a preview page showing all three

Parameters
    user    GitHub username (default: fevnem)
    theme   dark | light (default: dark) — the reader's OS theme decides

Every response is a Complete SVG, including errors: a README embed must never
show a broken-image icon, so a failure still returns a drawable card.
"""

from __future__ import annotations

import html
import json
import math
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

VERSION = "1.0.0"
DEFAULT_USER = "fevnem"
HTTP_TIMEOUT = 15
USER_AGENT = "github-stats/1.0 (+https://github.com/fevnem/github-stats)"

# Served from the CDN for 10 minutes, then revalidated in the background: fresh
# enough to call "live", polite enough that a profile view never hammers GitHub.
CACHE_HEADERS = [("Cache-Control",
                  "public, max-age=300, s-maxage=600, stale-while-revalidate=900")]
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

# ---------------------------------------------------------------------------
# data
# ---------------------------------------------------------------------------

TD_RE = re.compile(r"<td\b[^>]*>", re.I)
ATTR_RE = re.compile(r'([A-Za-z-]+)="([^"]*)"')
TIP_RE = re.compile(r"<tool-tip\b[^>]*\bfor=\"([^\"]+)\"[^>]*>(.*?)</tool-tip>",
                    re.I | re.S)
COMPONENT_RE = re.compile(r"contribution-day-component-(\d+)-(\d+)")
COUNT_RE = re.compile(r"(\d+|No)\s+contribution", re.I)
USER_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$")

GRAPHQL_QUERY = ("query($login:String!){user(login:$login){contributionsCollection"
                 "{contributionCalendar{totalContributions,weeks{contributionDays"
                 "{contributionCount,date}}}}}}")


class StatsUnavailable(RuntimeError):
    """Raised when the contribution calendar cannot be read from any source."""


def _get(url, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                              "Accept": "text/html",
                                              **(headers or {})})
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as r:
        return r.read().decode("utf-8", "replace")


def _from_html(user):
    """Parse the public contribution calendar. No token, no configuration."""
    page = _get(f"https://github.com/users/{urllib.parse.quote(user)}/contributions")
    counts = {}
    for tip in TIP_RE.finditer(page):
        m = COUNT_RE.search(re.sub(r"<[^>]+>", " ", tip.group(2)))
        if not m:
            continue
        token = m.group(1)
        counts[tip.group(1)] = 0 if token.lower() == "no" else int(token)
    days = []
    for tag in TD_RE.finditer(page):
        attrs = dict(ATTR_RE.findall(tag.group(0)))
        date = attrs.get("data-date")
        day_id = attrs.get("id", "")
        if not date or not day_id:
            continue
        comp = COMPONENT_RE.search(day_id)
        days.append({
            "date": date,
            "contributionCount": counts.get(day_id, 0),
            "dow": int(comp.group(1)) if comp else 0,
            "week": int(comp.group(2)) if comp else 0,
        })
    if not days:
        raise StatsUnavailable("contribution calendar markup not recognised")
    days.sort(key=lambda d: d["date"])
    return days, "html"


def _from_graphql(user):
    """Optional path: exact totals via the GraphQL API when a token is present."""
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise StatsUnavailable("no token configured")
    body = json.dumps({"query": GRAPHQL_QUERY, "variables": {"login": user}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql", data=body,
        headers={"User-Agent": USER_AGENT, "Authorization": f"bearer {token}",
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as r:
        payload = json.loads(r.read().decode("utf-8", "replace"))
    cal = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days, week = [], 0
    for wi, wk in enumerate(cal["weeks"]):
        for di, day in enumerate(wk["contributionDays"]):
            days.append({"date": day["date"],
                         "contributionCount": day["contributionCount"],
                         "dow": di, "week": wi})
    days.sort(key=lambda d: d["date"])
    return days, "graphql"


def fetch_calendar(user):
    """Days (chronological) plus which source produced them.

    The public HTML comes first: it needs no secret and is exactly what GitHub
    itself shows. A token, if one happens to be set, is only a safety net for
    the day that markup changes.
    """
    try:
        return _from_html(user)
    except (StatsUnavailable, urllib.error.URLError, OSError, ValueError) as first:
        try:
            return _from_graphql(user)
        except Exception:                                        # noqa: BLE001
            raise StatsUnavailable(str(first)) from first


def analyse(days):
    """total, current streak, longest streak, [(week_start_date, week_total)]."""
    total = sum(d["contributionCount"] for d in days)
    longest = run = 0
    for d in days:
        run = run + 1 if d["contributionCount"] > 0 else 0
        longest = max(longest, run)
    seq = list(days)
    if seq and seq[-1]["contributionCount"] == 0:      # today may be unfinished
        seq.pop()
    current = 0
    for d in reversed(seq):
        if d["contributionCount"] > 0:
            current += 1
        else:
            break
    weeks = [(days[i]["date"], sum(x["contributionCount"] for x in days[i:i + 7]))
             for i in range(0, len(days), 7)]
    return total, current, longest, weeks


def as_calendar(days, total):
    """Reshape into GitHub's own week grouping so the field renders identically."""
    buckets = {}
    for d in days:
        buckets.setdefault(d["week"], []).append(d)
    weeks = []
    for key in sorted(buckets):
        week = sorted(buckets[key], key=lambda d: d["dow"])
        weeks.append({"contributionDays": week})
    return {"totalContributions": total, "weeks": weeks}


# ---------------------------------------------------------------------------
# cards
# ---------------------------------------------------------------------------

def streak_card(p, user, total, current, longest):
    W, H, third = 520, 200, 520 / 3
    who = html.escape(user)
    cols = [(total, "TOTAL CONTRIBUTIONS"), (current, "CURRENT STREAK"),
            (longest, "LONGEST STREAK")]
    parts = []
    for i, (value, label) in enumerate(cols):
        cx = third * (i + 0.5)
        parts.append(f'<text x="{cx:.0f}" y="112" text-anchor="middle"'
                     f' font-family="{SANS}" font-size="42" font-weight="800"'
                     f' fill="url(#sg)">{value}</text>')
        parts.append(f'<text x="{cx:.0f}" y="141" text-anchor="middle"'
                     f' font-family="{MONO}" font-size="9.5" letter-spacing="1.4"'
                     f' fill="{p["dim"]}">{label}</text>')
        if i:
            parts.append(f'<line x1="{third * i:.0f}" y1="72" x2="{third * i:.0f}"'
                         f' y2="148" stroke="{p["div"]}" stroke-width="1.2"/>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="st sd">
<title id="st">Contribution streak</title>
<desc id="sd">{total} contributions, current streak {current} days, longest streak {longest} days.</desc>
<defs>
<clipPath id="scard"><rect width="{W}" height="{H}" rx="12"/></clipPath>
<linearGradient id="sg" gradientUnits="userSpaceOnUse" x1="30" y1="0" x2="490" y2="0">
<stop offset="0" stop-color="{p['a1']}"/><stop offset=".55" stop-color="{p['a2']}"/>
<stop offset="1" stop-color="{p['a3']}"/></linearGradient>
<linearGradient id="sh" x1="0" y1="0" x2="1" y2="0">
<stop offset="0" stop-color="{p['a1']}" stop-opacity="0"/>
<stop offset=".45" stop-color="{p['a1']}" stop-opacity=".95"/>
<stop offset="1" stop-color="{p['a3']}" stop-opacity="0"/></linearGradient>
</defs>
<rect width="{W}" height="{H}" rx="12" fill="{p['bg']}" stroke="{p['border']}"/>
<g clip-path="url(#scard)"><rect x="0" y="0" width="{W}" height="4" fill="url(#sh)"/></g>
<text x="{W / 2:.0f}" y="44" text-anchor="middle" font-family="{MONO}" font-size="10.5" letter-spacing="2" fill="{p['dim']}">CONTRIBUTION STREAK</text>
{"".join(parts)}
<text x="24" y="{H - 20}" font-family="{MONO}" font-size="10" letter-spacing="2.4" fill="{p['dim']}">LIVE</text>
<text x="{W - 24}" y="{H - 20}" text-anchor="end" font-family="{MONO}" font-size="10" letter-spacing="1.6" fill="{p['dim']}">github.com/{who}</text>
</svg>
'''


def activity_card(p, user, weeks):
    W, H = 880, 250
    L, R, T, B = 58, 28, 70, 48
    iw, ih = W - L - R, H - T - B
    totals = [w[1] for w in weeks]
    peak = max(totals) or 1
    axis_max = max(10, -(-int(peak * 1.12) // 10) * 10)   # round the top up to 10s
    scale = ih / axis_max
    step = iw / max(1, len(totals) - 1)
    pts = [(L + i * step, T + ih - v * scale) for i, v in enumerate(totals)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = ("M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
            + f" L{L + iw:.1f} {T + ih} L{L} {T + ih} Z")
    grid = "".join(
        f'<line x1="{L}" y1="{T + ih * i / 4:.0f}" x2="{L + iw}" y2="{T + ih * i / 4:.0f}"'
        f' stroke="{p["grid"]}" stroke-width="1"/>' for i in range(5))
    grid += (f'<text x="{L - 12}" y="{T + 4}" text-anchor="end" font-family="{MONO}"'
             f' font-size="10" fill="{p["dim"]}">{axis_max}</text>'
             f'<text x="{L - 12}" y="{T + ih + 4}" text-anchor="end"'
             f' font-family="{MONO}" font-size="10" fill="{p["dim"]}">0</text>')

    marks, seen = [], set()
    for i, (date, _) in enumerate(weeks):
        month = date[:7]
        if month not in seen:
            seen.add(month)
            marks.append((i, month))
    if len(marks) > 1 and marks[0][1][5:] == marks[-1][1][5:]:
        marks.pop()                                  # trailing partial month
    labels = [f'<text x="{L + i * step:.0f}" y="{H - 18}" font-family="{MONO}"'
              f' font-size="10" fill="{p["dim"]}" letter-spacing="1">'
              f'{MONTHS[int(m[5:7]) - 1]}</text>' for i, m in marks]
    px, py = pts[totals.index(peak)]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="at ad">
<title id="at">Contribution activity</title>
<desc id="ad">Weekly contribution totals for the last 12 months; peak week {peak}.</desc>
<defs>
<linearGradient id="af" x1="0" y1="0" x2="0" y2="1">
<stop offset="0" stop-color="{p['a2']}" stop-opacity=".55"/>
<stop offset="1" stop-color="{p['a1']}" stop-opacity="0"/></linearGradient>
<linearGradient id="al" x1="0" y1="0" x2="1" y2="0">
<stop offset="0" stop-color="{p['a3']}"/><stop offset="1" stop-color="{p['a1']}"/></linearGradient>
</defs>
<rect width="{W}" height="{H}" rx="12" fill="{p['bg']}" stroke="{p['border']}"/>
{grid}
<path d="{area}" fill="url(#af)"/>
<polyline points="{line}" fill="none" stroke="url(#al)" stroke-width="2.4" stroke-linejoin="round"/>
<circle cx="{px:.1f}" cy="{py:.1f}" r="4" fill="{p['a1']}"/>
<text x="{px - 10:.0f}" y="{py - 12:.0f}" text-anchor="end" font-family="{MONO}" font-size="10" fill="{p['ink']}" letter-spacing="1">peak {peak}/week</text>
<line x1="{L}" y1="{T + ih}" x2="{L + iw}" y2="{T + ih}" stroke="{p['border']}" stroke-width="1"/>
{"".join(labels)}
<text x="{L}" y="42" font-family="{MONO}" font-size="11" letter-spacing="2.4" fill="{p['dim']}">ACTIVITY &#183; WEEKLY TOTALS, LAST 12 MONTHS</text>
</svg>
'''


# ---------------------------------------------------------------------------
# 3-D contribution field (isometric)
# ---------------------------------------------------------------------------

FW, FH = 900, 400
FOX, FOY = 190.0, 126.0      # far corner of the base plane
FTW, FTH = 20.0, 10.0        # isometric tile width / height (2:1)
BZ = 3.05                    # pixels of height per contribution
DAYS, WEEKS = 7, 53


def _iso(w, d, h=0.0):
    return (FOX + (w + d) * (FTW / 2), FOY + (w - d) * (FTH / 2) - h)


def _shade(hex_color, factor):
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % (int(r * factor), int(g * factor), int(b * factor))


def _level(count, cuts):
    for i, c in enumerate(cuts):
        if count >= c:
            return i + 1
    return 0


def _column(w, d, count, pal, cuts):
    h = count * BZ
    top, r, f, b = _iso(w, d, h), _iso(w + 1, d, h), _iso(w, d + 1, h), _iso(w + 1, d + 1, h)
    rb, fb, bb = _iso(w + 1, d), _iso(w, d + 1), _iso(w + 1, d + 1)
    lv = _level(count, cuts)
    if lv == 0:
        top_fill, side = pal["empty_top"], pal["empty"]
    else:
        top_fill, side = pal["scale"][lv - 1]
    side_b = _shade(side, 0.74)
    svg = ""
    if count:
        svg += (f'<path d="M{r[0]:.1f} {r[1]:.1f} L{b[0]:.1f} {b[1]:.1f} '
                f'L{bb[0]:.1f} {bb[1]:.1f} L{rb[0]:.1f} {rb[1]:.1f} Z" fill="{side}"/>'
                f'<path d="M{f[0]:.1f} {f[1]:.1f} L{b[0]:.1f} {b[1]:.1f} '
                f'L{bb[0]:.1f} {bb[1]:.1f} L{fb[0]:.1f} {fb[1]:.1f} Z" fill="{side_b}"/>')
    svg += (f'<path d="M{top[0]:.1f} {top[1]:.1f} L{r[0]:.1f} {r[1]:.1f} '
            f'L{b[0]:.1f} {b[1]:.1f} L{f[0]:.1f} {f[1]:.1f} Z" fill="{top_fill}"'
            + (f' stroke="{pal["plane_edge"]}" stroke-opacity="1"'
               f' stroke-width="1"' if lv == 0 else '') + '/>')
    return (w - d, svg)


def field_svg(mode, cal):
    pal = FIELD_THEMES[mode]
    weeks = cal["weeks"]
    days = [d for wk in weeks for d in wk["contributionDays"]]
    peak = max(d["contributionCount"] for d in days) or 1
    cuts = sorted({max(1, math.ceil(peak * f)) for f in (.10, .25, .48, .75)})

    cols = []
    for wi, wk in enumerate(weeks):
        for di, day in enumerate(wk["contributionDays"]):
            cols.append(_column(wi, di, day["contributionCount"], pal, cuts))
    cols.sort(key=lambda c: c[0])                     # back-to-front overlap

    a, b, c, d = _iso(0, 0), _iso(WEEKS, 0), _iso(WEEKS, DAYS), _iso(0, DAYS)
    plane = (f'<path d="M{a[0]:.1f} {a[1]:.1f} L{b[0]:.1f} {b[1]:.1f} '
             f'L{c[0]:.1f} {c[1]:.1f} L{d[0]:.1f} {d[1]:.1f} Z" fill="{pal["plane"]}"'
             f' stroke="{pal["plane_edge"]}" stroke-width="1"/>')

    ticks = []
    marks, seen = [], set()
    for wi, wk in enumerate(weeks):
        m = wk["contributionDays"][0]["date"][:7]
        if m not in seen:
            seen.add(m)
            marks.append((wi, m))
    if len(marks) > 1 and marks[0][1][5:] == marks[-1][1][5:]:
        marks.pop()                                   # trailing partial month
    for wi, m in marks:
        x, y = _iso(wi, DAYS + 0.05)
        ticks.append(f'<text x="{x - 4:.0f}" y="{y + 17:.0f}" font-size="14"'
                     f' font-family="ui-monospace,Menlo,monospace" fill="{pal["tick"]}"'
                     f' letter-spacing="1">{MONTHS[int(m[5:7]) - 1]}</text>')

    legend = [f'<text x="{a[0] - 178:.0f}" y="{FH - 44}" font-size="11"'
              f' font-family="ui-monospace,Menlo,monospace" fill="{pal["dim"]}"'
              f' letter-spacing="1.4">LESS</text>']
    for i in range(5):
        fill = pal["empty_top"] if i == 0 else pal["scale"][i - 1][0]
        legend.append(f'<rect x="{a[0] - 134 + i * 19:.0f}" y="{FH - 56}" width="14"'
                      f' height="14" rx="3" fill="{fill}" stroke="{pal["plane_edge"]}"'
                      f' stroke-width=".7"/>')
    legend.append(f'<text x="{a[0] - 134 + 5 * 19 + 4:.0f}" y="{FH - 44}" font-size="11"'
                  f' font-family="ui-monospace,Menlo,monospace" fill="{pal["dim"]}"'
                  f' letter-spacing="1.4">MORE</text>')
    legend.append(f'<text x="{a[0] - 178:.0f}" y="{FH - 68}" font-size="11"'
                  f' font-family="ui-monospace,Menlo,monospace" fill="{pal["dim"]}"'
                  f' letter-spacing="1.4">CONTRIBUTIONS PER DAY</text>')

    total = str(cal["totalContributions"])
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {FW} {FH}" width="{FW}" height="{FH}" role="img" aria-labelledby="ct cd">
<title id="ct">Contribution calendar, 3-D</title>
<desc id="cd">{cal['totalContributions']} contributions over the last 12 months, drawn as an isometric bar field.</desc>
<defs>
<linearGradient id="cbg" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="{pal['bg0']}"/><stop offset="1" stop-color="{pal['bg1']}"/></linearGradient>
<filter id="cglow" x="-12%" y="-12%" width="124%" height="128%">
  <feDropShadow dx="0" dy="10" stdDeviation="12" flood-color="#7C3AED" flood-opacity=".3"/></filter>
</defs>
<rect width="{FW}" height="{FH}" fill="url(#cbg)"/>
<g filter="url(#cglow)">{plane}{"".join(c[1] for c in cols)}</g>
{"".join(ticks)}
<text x="30" y="56" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" font-size="12" letter-spacing="3" fill="{pal['dim']}">CONTRIBUTION FIELD &#183; LAST 12 MONTHS</text>
<text x="30" y="118" font-family="'Segoe UI',system-ui,-apple-system,Arial,sans-serif" font-size="46" font-weight="800" fill="{pal['total']}">{total}</text>
<text x="{30 + len(total) * 27 + 10}" y="118" font-family="ui-monospace,Menlo,monospace" font-size="13" letter-spacing="2.5" fill="{pal['dim']}">CONTRIBUTIONS</text>
{"".join(legend)}
</svg>
'''


# ---------------------------------------------------------------------------
# errors, router, adapters
# ---------------------------------------------------------------------------

def error_card(kind, mode, message):
    """A drawable card, never a broken image: HTTP 200 with the failure inside."""
    size = {"streak": (520, 200), "activity": (880, 250), "field": (900, 400)}
    W, H = size.get(kind, (520, 200))
    p = CARD_THEMES.get(mode, CARD_THEMES["dark"])
    msg = html.escape(message[:70])
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="et ed">
<title id="et">Stats unavailable</title>
<desc id="ed">{msg}</desc>
<rect width="{W}" height="{H}" rx="12" fill="{p['bg']}" stroke="{p['border']}"/>
<text x="{W / 2:.0f}" y="{H / 2 - 6:.0f}" text-anchor="middle" font-family="{MONO}" font-size="13" letter-spacing="2" fill="{p['dim']}">STATS TEMPORARILY UNAVAILABLE</text>
<text x="{W / 2:.0f}" y="{H / 2 + 20:.0f}" text-anchor="middle" font-family="{MONO}" font-size="11" fill="{p['ink']}">{msg}</text>
</svg>
'''


def preview_html(user):
    """A small landing page: useful for eyeballing the live cards."""
    who = html.escape(user)
    base = f"?user={urllib.parse.quote(user)}"
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>github-stats — {who}</title>
<style>
:root {{ color-scheme: dark light; }}
body {{ margin:0; padding:48px 24px; background:#0d1117; color:#e6edf3;
       font:15px/1.6 -apple-system,system-ui,'Segoe UI',sans-serif; }}
h1 {{ font-size:20px; letter-spacing:.4px; margin:0 0 4px; }}
p  {{ color:#8b949e; margin:0 0 32px; }}
code {{ background:#161b22; border:1px solid #30363d; border-radius:6px;
        padding:2px 6px; color:#e6edf3; }}
img {{ display:block; max-width:100%; height:auto; margin:0 0 20px; }}
@media (prefers-color-scheme: light) {{
  body {{ background:#ffffff; color:#1f2328; }}
  p {{ color:#59636e; }}
  code {{ background:#f6f8fa; border-color:#d1d9e0; }}
}}
</style></head><body>
<h1>github-stats</h1>
<p>Live contribution stats for <strong>{who}</strong> — no token, no build step.</p>
<img width="100%" src="/field{base}" alt="Contribution field">
<img src="/streak{base}" alt="Streak">
<img width="100%" src="/activity{base}" alt="Activity">
<p>Embed as <code>/streak{base}</code> · <code>/activity{base}</code> · <code>/field{base}</code></p>
</body></html>
'''


def render(path, query):
    """(status, content_type, body, extra_headers) — the whole service."""
    params = {k: v[0] for k, v in urllib.parse.parse_qs(query).items()}
    segments = [s for s in path.split("/") if s]
    kind = segments[-1] if segments else ""
    if kind in ("api", "index"):
        kind = ""
    if kind not in ("streak", "activity", "field"):
        kind = params.get("type", "") if params.get("type") in (
            "streak", "activity", "field") else kind

    user = params.get("user", DEFAULT_USER)
    mode = "light" if params.get("theme") == "light" else "dark"

    if kind not in ("streak", "activity", "field"):
        return (200, "text/html; charset=utf-8",
                preview_html(user if USER_RE.match(user) else DEFAULT_USER).encode(),
                CACHE_HEADERS)

    if not USER_RE.match(user):
        return (200, "image/svg+xml; charset=utf-8",
                error_card(kind, mode, "invalid username").encode(),
                ERROR_CACHE_HEADERS)

    try:
        days, _source = fetch_calendar(user)
        total, current, longest, weeks = analyse(days)
        if kind == "streak":
            body = streak_card(CARD_THEMES[mode], user, total, current, longest)
        elif kind == "activity":
            body = activity_card(CARD_THEMES[mode], user,
                                 weeks[1:] if len(weeks) > 52 else weeks)
        else:
            body = field_svg(mode, as_calendar(days, total))
        return (200, "image/svg+xml; charset=utf-8", body.encode(), CACHE_HEADERS)
    except Exception as exc:                                     # noqa: BLE001
        return (200, "image/svg+xml; charset=utf-8",
                error_card(kind, mode, f"github read failed: {exc}").encode(),
                ERROR_CACHE_HEADERS)


def app(environ, start_response):
    """WSGI entrypoint (Vercel accepts this alongside the handler below)."""
    status, ctype, body, extra = render(environ.get("PATH_INFO", "/"),
                                        environ.get("QUERY_STRING", ""))
    start_response(f"{status} OK", [("Content-Type", ctype),
                                    ("Access-Control-Allow-Origin", "*"),
                                    ("X-Stats-Version", VERSION)] + extra)
    return [body]


try:                                    # pragma: no cover - Vercel's entrypoint
    from http.server import BaseHTTPRequestHandler

    class handler(BaseHTTPRequestHandler):        # noqa: N801 (Vercel's name)
        """Vercel's Python runtime entrypoint — dispatches to render()."""

        def do_GET(self):
            parsed = urllib.parse.urlsplit(self.path)
            status, ctype, body, extra = render(parsed.path, parsed.query)
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("X-Stats-Version", VERSION)
            for key, value in extra:
                self.send_header(key, value)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):             # keep Vercel logs tidy
            pass
except Exception:                                # pragma: no cover
    pass


if __name__ == "__main__":                        # pragma: no cover
    from wsgiref.simple_server import make_server

    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8899
    print(f"github-stats {VERSION} on http://127.0.0.1:{port}/")
    make_server("127.0.0.1", port, app).serve_forever()
