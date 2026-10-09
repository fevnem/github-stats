"""The router, and the entrypoints that expose it.

`render()` is a pure function of (path, query) — every host adapter is a thin
wrapper around it. Nothing here depends on being serverless, which is why the same
code runs on a VPS, in a container, or on Vercel.
"""

from __future__ import annotations

import urllib.parse

from github_stats import palettes, styles, webui
from github_stats.cards import streak_card
from github_stats.config import CACHE_HEADERS, ERROR_CACHE_HEADERS, KINDS, VERSION
from github_stats.errors import error_card
from github_stats.field import field_svg
from github_stats.github import USER_RE, fetch_calendar
from github_stats.stats import analyse, as_calendar

SVG = "image/svg+xml; charset=utf-8"
HTML = "text/html; charset=utf-8"


def _params(query: str) -> dict[str, str]:
    return {key: values[0] for key, values in
            urllib.parse.parse_qs(query, keep_blank_values=True).items()}


def render(path: str, query: str) -> tuple[int, str, bytes, list[tuple[str, str]]]:
    """(status, content_type, body, extra_headers) for one request."""
    params = _params(query)
    segments = [segment for segment in path.split("/") if segment]

    kind = segments[-1] if segments else ""
    if kind in ("api", "index"):
        kind = ""
    if kind not in KINDS:
        requested = params.get("type", "")
        kind = requested if requested in KINDS else ""

    mode = "light" if params.get("theme") == "light" else "dark"
    palette_name = params.get("palette", palettes.DEFAULT_PALETTE)
    if not palettes.is_palette(palette_name):
        palette_name = palettes.DEFAULT_PALETTE
    style = params.get("style", styles.DEFAULT_STYLE)
    if not styles.is_style(style):
        style = styles.DEFAULT_STYLE
    motion = params.get("motion", "1") != "0"

    if kind not in KINDS:                       # anything else is the landing page
        return 200, HTML, webui.page().encode("utf-8"), CACHE_HEADERS

    colour = palettes.resolve(palette_name, mode)
    user = params.get("user", "").strip()

    if not user:
        return (200, SVG,
                error_card(kind, colour, "add ?user=username to this URL").encode(),
                ERROR_CACHE_HEADERS)
    if not USER_RE.match(user):
        return (200, SVG,
                error_card(kind, colour, f"'{user[:24]}' is not a GitHub username").encode(),
                ERROR_CACHE_HEADERS)

    try:
        days, _source = fetch_calendar(user)
        total, current, longest, weeks = analyse(days)
        if kind == "streak":
            body = streak_card(colour, user, total, current, longest)
        elif kind == "activity":
            body = styles.render(style, colour, user, weeks, days, motion)
        else:
            body = field_svg(palettes.resolve_field(palette_name, mode),
                             as_calendar(days, total))
    except Exception as exc:                    # noqa: BLE001 - always render something
        body = error_card(kind, colour, f"GitHub read failed: {exc}")

    return 200, SVG, body.encode("utf-8"), CACHE_HEADERS


def _headers(content_type: str, extra: list[tuple[str, str]]) -> list[tuple[str, str]]:
    return [("Content-Type", content_type),
            ("Access-Control-Allow-Origin", "*"),
            ("X-Stats-Version", VERSION)] + extra


def app(environ, start_response):
    """WSGI entrypoint — used by server.py and by any WSGI container."""
    status, content_type, body, extra = render(
        environ.get("PATH_INFO", "/"), environ.get("QUERY_STRING", ""))
    start_response(f"{status} {'OK' if status == 200 else 'Error'}",
                   _headers(content_type, extra))
    return [body]


try:
    from http.server import BaseHTTPRequestHandler

    class handler(BaseHTTPRequestHandler):   # noqa: N801 - Vercel's expected name
        """Vercel's Python runtime entrypoint: a request handler, not a framework."""

        protocol_version = "HTTP/1.1"

        def do_GET(self):
            parsed = urllib.parse.urlsplit(self.path)
            status, content_type, body, extra = render(parsed.path, parsed.query)
            self.send_response(status)
            for key, value in _headers(content_type, extra):
                self.send_header(key, value)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass
except ImportError:                          # pragma: no cover
    handler = None                           # type: ignore[assignment]
