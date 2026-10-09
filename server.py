#!/usr/bin/env python3
"""Run the service anywhere Python runs: a VPS, a container, your laptop.

    python3 server.py                      # 0.0.0.0:8000
    python3 server.py --port 9000          # another port
    python3 server.py --host 127.0.0.1     # local only

Standard library only — no virtualenv, no dependencies, no build.
"""

from __future__ import annotations

import argparse
import pathlib
import sys
from wsgiref.simple_server import WSGIRequestHandler, make_server

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from github_stats.app import app  # noqa: E402
from github_stats.config import VERSION  # noqa: E402


class QuietHandler(WSGIRequestHandler):
    """Log the request line only — enough to see traffic, not a wall of noise."""

    def log_message(self, fmt, *args):
        sys.stderr.write("  %s %s\n" % (self.address_string(), fmt % args))


def main() -> int:
    parser = argparse.ArgumentParser(description="github-stats server")
    parser.add_argument("--host", default="0.0.0.0", help="bind address")
    parser.add_argument("--port", type=int, default=8000, help="bind port")
    args = parser.parse_args()

    print(f"github-stats {VERSION}")
    print(f"  listening on http://{args.host}:{args.port}/")
    print("  routes: /  /streak  /activity  /field    params: ?user= &theme=dark|light")
    try:
        make_server(args.host, args.port, app, handler_class=QuietHandler).serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
