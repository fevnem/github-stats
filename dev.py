#!/usr/bin/env python3
"""Run the service locally exactly as it runs on Vercel.

    python3 dev.py [port]        # default 8899

Serves the same render() the serverless function does, through wsgiref — no
framework, no dependency, nothing to install.
"""
import pathlib
import sys
from wsgiref.simple_server import make_server

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "api"))

from index import VERSION, app  # noqa: E402

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8899
    print(f"github-stats {VERSION} -> http://127.0.0.1:{port}/")
    print("  /streak  /activity  /field  ?user=  &theme=light")
    make_server("127.0.0.1", port, app).serve_forever()
