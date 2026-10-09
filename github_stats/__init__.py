"""github-stats — live GitHub contribution stats, rendered as SVG.

A dependency-free service that turns any GitHub username into embeddable stat
cards. Ships as a standard-library WSGI app, so the same code runs on a VPS, in
Docker, or as a Vercel serverless function.
"""

from github_stats.app import app as wsgi
from github_stats.app import handler, render  # noqa: F401
from github_stats.config import VERSION  # noqa: F401

__all__ = ["wsgi", "handler", "render", "VERSION"]
__version__ = VERSION
