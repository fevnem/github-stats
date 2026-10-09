<div align="center">

# github-stats

**Live GitHub contribution stats as SVG — for any profile README.**

Type a username, get three cards, copy the snippet. Every request re-reads GitHub,
so the numbers are current: nothing to schedule, nothing to keep in sync.

<img alt="License" src="https://img.shields.io/badge/license-MIT-0a0710?style=flat-square&logo=opensourceinitiative&logoColor=FF00F6"> <img alt="Python 3.9+" src="https://img.shields.io/badge/python-3.9%2B-0a0710?style=flat-square&logo=python&logoColor=FF00F6"> <img alt="Zero dependencies" src="https://img.shields.io/badge/dependencies-0-0a0710?style=flat-square&logo=checkmarx&logoColor=FF00F6"> <img alt="No token required" src="https://img.shields.io/badge/token-not%20required-0a0710?style=flat-square&logo=github&logoColor=FF00F6"> <img alt="Deploy" src="https://img.shields.io/badge/deploy-Vercel%20%C2%B7%20Docker%20%C2%B7%20VPS-0a0710?style=flat-square&logo=docker&logoColor=FF00F6">

<img width="100%" alt="The github-stats web UI: type a username, preview the cards, copy the embed" src="assets/webui.png">

</div>

---

## The three cards

Everything is generated at request time from GitHub's own contribution calendar.

### Contribution field — `/field?user=NAME`

Every day of the last year as an isometric tile. Height and colour both encode that
day's count, and columns are drawn back-to-front so nearer tiles overlap farther
ones. Both themes share the geometry, so this swaps cleanly with the reader's OS
setting.

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/example-field.svg">
    <source media="(prefers-color-scheme: light)" srcset="assets/example-field-light.svg">
    <img width="100%" alt="Isometric 3-D contribution field" src="assets/example-field.svg">
  </picture>
</p>

### Streak — `/streak?user=NAME`

Totals, current streak and longest streak. A zero on the final day reads as "today
is not over yet" rather than the end of a streak, which is what a reader expects to
see mid-morning.

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/example-streak.svg">
    <source media="(prefers-color-scheme: light)" srcset="assets/example-streak-light.svg">
    <img alt="Contribution streak" src="assets/example-streak.svg">
  </picture>
</p>

### Activity — `/activity?user=NAME`

Weekly totals for the year on an honest axis: the top is rounded up to the next ten
so the shape is never exaggerated, and the peak week is labelled.

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/example-activity.svg">
    <source media="(prefers-color-scheme: light)" srcset="assets/example-activity-light.svg">
    <img width="100%" alt="Weekly contribution totals over twelve months" src="assets/example-activity.svg">
  </picture>
</p>

<sub>The examples above are committed output for <code>sindresorhus</code> — real
renders, not mockups.</sub>

## Quick start

```bash
# no install: just ask a deployment
curl "https://YOUR-HOST/streak?user=NAME" -o streak.svg

# or run it yourself — standard library only, nothing to pip install
python3 server.py --port 8000
# then open http://localhost:8000/?user=torvalds
```

## Endpoints

| Route | Returns |
| --- | --- |
| `/?user=NAME` | the web UI — preview every card and copy the embed |
| `/streak?user=NAME` | total contributions, current streak, longest streak |
| `/activity?user=NAME` | weekly totals over the last twelve months |
| `/field?user=NAME` | the isometric 3-D contribution field |

| Parameter | Values | Default | Notes |
| --- | --- | --- | --- |
| `user` | any GitHub username | *required* | the service is generic — there is no default user |
| `theme` | `dark`, `light` | `dark` | accepted by every route |

Cards return `image/svg+xml`, the UI returns `text/html`, and CORS is open to every
origin. Responses are cached 5 minutes in the browser and 10 at the edge with
stale-while-revalidate: fresh enough to call live, polite enough that a profile
view never hammers GitHub.

## Embed

```html
<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)"  srcset="https://YOUR-HOST/field?user=NAME&theme=dark">
    <source media="(prefers-color-scheme: light)" srcset="https://YOUR-HOST/field?user=NAME&theme=light">
    <img width="100%" alt="Contribution field" src="https://YOUR-HOST/field?user=NAME&theme=dark">
  </picture>
</p>
```

Swap `/field` for `/streak` or `/activity`. The web UI builds this snippet for you,
already pointing at the right host.

## Deploy

A standard-library WSGI app, so it runs anywhere Python 3.9+ runs. Pick whatever you
already have.

| Host | How | Time |
| --- | --- | --- |
| **Vercel** | import the repo, framework "Other", deploy | ~1 min |
| **Docker** | `docker compose up -d` | ~1 min |
| **VPS** | `python3 server.py --port 8000` + the unit below | ~2 min |
| **Any PaaS** | point it at `server.py`, or the WSGI callable `github_stats.app.app` | — |

<details>
<summary><b>Docker</b></summary>

```bash
docker build -t github-stats .
docker run -d -p 8000:8000 --name github-stats github-stats
```

Or `docker compose up -d` (see `docker-compose.yml`). The image is
`python:3.12-alpine`, runs as a non-root user and has a healthcheck.
</details>

<details>
<summary><b>VPS, bare Python</b></summary>

```bash
python3 server.py --host 0.0.0.0 --port 8000
```

Put nginx or Caddy in front, and use a unit like this to survive a reboot:

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
</details>

<details>
<summary><b>Vercel</b></summary>

Import this repository, choose **Other** as the framework if asked, then deploy.
`api/index.py` is detected as a Python function and `vercel.json` maps the pretty
paths. No environment variables to set.
</details>

## Configuration

None required — that is rather the point. Optional: set `GH_TOKEN` (or
`GITHUB_TOKEN`) so the service can fall back to the GitHub GraphQL API when the
public calendar page cannot be parsed. It is only ever a fallback, so everything
works without it.

## How it works

```
browser / README
        │  /streak?user=NAME
        ▼
  github_stats.app.render ────► github_stats.github.fetch_calendar
        │                              │
        │                              ├─ github.com/users/NAME/contributions  (public, no auth)
        │                              └─ api.github.com/graphql              (only if GH_TOKEN)
        ▼
  github_stats.cards · github_stats.field ────► image/svg+xml
```

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
api/index.py   Vercel shim (puts the repo root on sys.path, re-exports the app)
server.py      VPS / container entrypoint (wsgiref)
```

Three things worth calling out:

- **No token.** The calendar is read from `github.com/users/<user>/contributions` —
  the same public HTML GitHub renders on every profile. `data-date` gives the day
  and the tool-tip text gives the count. Nothing to leak, nothing to rotate.
- **Errors are drawn, not thrown.** A failure returns a card of the expected size
  with HTTP 200, so an embed in someone's profile README never shows a
  broken-image icon.
- **A package, not a lambda.** `api/index.py` and `server.py` are thin adapters
  around one WSGI app, which is why this is not Vercel-only.

## License

MIT
