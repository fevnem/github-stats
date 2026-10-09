#!/usr/bin/env python3
"""Vercel serverless entrypoint.

Vercel turns every `.py` under `api/` into its own function. This one is a shim
so the real code can live in an ordinary package: put the repository root on
`sys.path`, then hand Vercel the WSGI app and the request-handler class it knows
how to detect.
"""

from __future__ import annotations

import pathlib
import sys

ROOT = str(pathlib.Path(__file__).resolve().parents[1])
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from github_stats.app import app  # noqa: E402,F401 - re-exported for Vercel
from github_stats.app import handler  # noqa: E402,F401
from github_stats.config import VERSION  # noqa: E402,F401

__all__ = ["app", "handler", "VERSION"]
