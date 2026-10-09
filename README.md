# github-stats

Live GitHub contribution stats as SVG — embeddable cards for any profile README.

Type a username, get three cards, copy the snippet. Every request re-reads GitHub,
so the numbers are current: there is nothing to schedule and nothing to keep in
sync.

**No token. No build step. No dependencies. No configuration.**

## What you get

| Route | Card |
| --- | --- |
| `/field?user=NAME` | the isometric 3-D contribution field — every day of the last year as a tile whose height and colour encode that day's count |
| `/streak?user=NAME` | total contributions, current streak, longest streak |
| `/activity?user=NAME` | weekly totals over the last twelve months |
| `/?user=NAME` | the web UI — preview all three and copy the embed |

`NAME` is required: the service is generic and has no default user.

### Parameters

| Name | Values | Default | Notes |
| --- | --- | --- | --- |
| `user` | any GitHub username | *required* | letters, digits and hyphens |
| `theme` | `dark`, `light` | `dark` | every route accepts it |

### Behaviour

- `image/svg+xml` for cards, `text/html` for the UI, CORS open to all origins.
- Cached 5 minutes in the browser, 10 at the edge, revalidated in the background.
  Fresh enough to call live, polite enough that a profile view never hammers GitHub.
- **Errors return a drawn card with HTTP 200.** A README embed never shows a
  broken-image icon — if GitHub is unreachable you get a card that says so.
- Both themes are drawn to the same geometry, so `<picture>` swaps them cleanly:

```html
<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)"  srcset="https://YOUR-HOST/field?user=NAME&theme=dark">
    <source media="(prefers-color-scheme: light)" srcset="https://YOUR-HOST/field?user=NAME&theme=light">
    <img width="100%" alt="Contribution field" src="https://YOUR-HOST/field?user=NAME&theme=dark">
  </picture>
</p>
```

## Deploy

It is a standard-library WSGI app, so it runs anywhere Python 3.9+ runs.

### Docker / any container host

```bash
docker build -t github-stats .
docker run -d -p 8000:8000 --name github-stats github-stats
```

Or with Compose: `docker compose up -d` (see `docker-compose.yml`).

### A VPS, bare Python

```bash
python3 server.py --host 0.0.0.0 --port 8000
```

Behind nginx or Caddy, plus a systemd unit if you want it to survive a reboot:

```ini
# /etc/systemd/system/github-stats.service
[Unit]
Description=github-stats
After=network-online.target

[Service]
WorkingDirectory=/opt/github-stats
ExecStart=/usr/bin/python3 server.py --host 127.0.0.1 --port 8000
Restart=always
User=www-data

[Install]
WantedBy=multi-user.target
```

### Vercel

Import this repository into Vercel, choose **Other** as the framework if asked, and
deploy. `api/index.py` is detected as a Python function and `vercel.json` maps the
pretty paths. No environment variables needed.

### Any other platform

Point it at `server.py`, or at the WSGI callable `github_stats.app.app`. Read the
port from `$PORT` if your host requires that (most do):

```bash
python3 server.py --port "${PORT:-8000}"
```

## Configuration

None is required.

Optional: set `GH_TOKEN` (or `GITHUB_TOKEN`) so the service can fall back to the
GitHub GraphQL API when the public calendar page cannot be parsed. It is only ever
used as a fallback, so the service works fine without it.

## How it works

```
github_stats/
  app.py       router + WSGI app + serverless handler
  github.py    calendar fetch and parse
  stats.py     totals, streaks, weekly buckets
  cards.py     streak and activity cards
  field.py     the isometric 3-D field
  webui.py     the landing page
  errors.py    drawn failure cards
  config.py    palettes, geometry, cache policy
```

- The contribution calendar is read from `github.com/users/<user>/contributions` —
  the same public HTML GitHub renders on every profile. `data-date` gives the day
  and the tool-tip text gives the count. No authentication, nothing to leak.
- `api/index.py` is a shim that puts the repository root on `sys.path` and
  re-exports the app, so the real code can live in a package instead of one
  serverless file.
- `server.py` wraps the same WSGI app in `wsgiref` for non-serverless hosts.

## License

MIT
