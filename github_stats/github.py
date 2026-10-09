"""Reading the contribution calendar.

The public calendar GitHub renders on every profile is the primary source: it
needs no token, no configuration and no secret. The GraphQL API is a fallback
used only when that markup stops being recognisable and a token happens to be
set in the environment.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request

from github_stats.config import HTTP_TIMEOUT, USER_AGENT

TD_RE = re.compile(r"<td\b[^>]*>", re.I)
ATTR_RE = re.compile(r'([A-Za-z-]+)="([^"]*)"')
TIP_RE = re.compile(r"<tool-tip\b[^>]*\bfor=\"([^\"]+)\"[^>]*>(.*?)</tool-tip>",
                    re.I | re.S)
COMPONENT_RE = re.compile(r"contribution-day-component-(\d+)-(\d+)")
COUNT_RE = re.compile(r"(\d+|No)\s+contribution", re.I)
TAG_RE = re.compile(r"<[^>]+>")

# GitHub usernames: letters, digits and single hyphens, never leading/trailing.
USER_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$")

GRAPHQL_QUERY = (
    "query($login:String!){user(login:$login){contributionsCollection"
    "{contributionCalendar{totalContributions,weeks{contributionDays"
    "{contributionCount,date}}}}}}"
)


class StatsUnavailable(RuntimeError):
    """Raised when the contribution calendar cannot be read from any source."""


def _get(url: str, headers: dict | None = None) -> str:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "text/html", **(headers or {})},
    )
    with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT) as response:
        return response.read().decode("utf-8", "replace")


def _parse_counts(page: str) -> dict[str, int]:
    """Map a contribution cell id to its count, read from the tool-tip text."""
    counts: dict[str, int] = {}
    for tip in TIP_RE.finditer(page):
        match = COUNT_RE.search(TAG_RE.sub(" ", tip.group(2)))
        if not match:
            continue
        token = match.group(1)
        counts[tip.group(1)] = 0 if token.lower() == "no" else int(token)
    return counts


def _from_html(user: str) -> tuple[list[dict], str]:
    """Parse the public contribution calendar. No token, no configuration."""
    page = _get(f"https://github.com/users/{urllib.parse.quote(user)}/contributions")
    counts = _parse_counts(page)
    days: list[dict] = []
    for tag in TD_RE.finditer(page):
        attrs = dict(ATTR_RE.findall(tag.group(0)))
        date, day_id = attrs.get("data-date"), attrs.get("id", "")
        if not date or not day_id:
            continue
        component = COMPONENT_RE.search(day_id)
        days.append({
            "date": date,
            "contributionCount": counts.get(day_id, 0),
            "dow": int(component.group(1)) if component else 0,
            "week": int(component.group(2)) if component else 0,
        })
    if not days:
        raise StatsUnavailable("contribution calendar markup not recognised")
    days.sort(key=lambda day: day["date"])
    return days, "html"


def _from_graphql(user: str) -> tuple[list[dict], str]:
    """Optional path: exact totals via the GraphQL API when a token is present."""
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise StatsUnavailable("no token configured")
    body = json.dumps({"query": GRAPHQL_QUERY, "variables": {"login": user}}).encode()
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={"User-Agent": USER_AGENT, "Authorization": f"bearer {token}",
                 "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT) as response:
        payload = json.loads(response.read().decode("utf-8", "replace"))
    calendar = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    if not calendar["weeks"]:
        raise StatsUnavailable(f"no contributions for {user}")
    days: list[dict] = []
    for week_index, week in enumerate(calendar["weeks"]):
        for day_index, day in enumerate(week["contributionDays"]):
            days.append({"date": day["date"],
                         "contributionCount": day["contributionCount"],
                         "dow": day_index, "week": week_index})
    days.sort(key=lambda day: day["date"])
    return days, "graphql"


def fetch_calendar(user: str) -> tuple[list[dict], str]:
    """Return days (chronological, one dict per day) and the source used.

    The public HTML comes first: it needs no secret and shows exactly what GitHub
    itself shows. A token, if one is set, only matters the day that markup
    changes — which is why the service works with no environment at all.
    """
    try:
        return _from_html(user)
    except (StatsUnavailable, urllib.error.URLError, OSError, ValueError) as html_error:
        try:
            return _from_graphql(user)
        except Exception:  # noqa: BLE001 - any failure means "no data available"
            raise StatsUnavailable(str(html_error)) from html_error
