# github-stats

Live GitHub contribution stats as SVG — for GitHub profile READMEs.

One dependency-free serverless function. **No token, no build step, no configuration:**
it reads the public contribution calendar that GitHub renders on every profile, so
there is no API key to create and no secret to leak.

```
/streak?user=fevnem      total contributions, current streak, longest streak
/activity?user=fevnem    weekly totals over the last 12 months
/field?user=fevnem       the isometric 3-D contribution field
/?user=fevnem            preview page showing all three
```

| Parameter | Default | Notes |
| --- | --- | --- |
| `user` | `fevnem` | any GitHub username |
| `theme` | `dark` | `dark` or `light` |

Cache is 5 minutes in the browser, 10 at the edge with stale-while-revalidate —
fresh enough to call live, polite enough that a profile view never hammers GitHub.
Responses are `image/svg+xml`, CORS-open, and **errors return a drawn card too**,
so a README embed never shows a broken-image icon.

## Deploy

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/fevnem/github-stats)

Import the repo, choose **Other** as the framework if asked, deploy. Vercel picks up
`api/index.py` as a Python function and `vercel.json` maps the pretty paths. Nothing
else to set — no environment variables are required.

Prefer the CLI:

```bash
npm i -g vercel
vercel --prod
```

## Embed

```html
<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)"  srcset="https://YOUR-PROJECT.vercel.app/field?user=fevnem&theme=dark">
    <source media="(prefers-color-scheme: light)" srcset="https://YOUR-PROJECT.vercel.app/field?user=fevnem&theme=light">
    <img width="100%" alt="Contribution field" src="https://YOUR-PROJECT.vercel.app/field?user=fevnem&theme=dark">
  </picture>
</p>
```

Swap `/field` for `/streak` or `/activity`. Only the artwork lives here; the
geometry is fixed and the numbers are live.

## Run locally

```bash
python3 dev.py            # http://127.0.0.1:8899
```

## How it works

- `api/index.py` — the whole service: one file, standard library only. It is a
  single file on purpose: on Vercel every `.py` under `api/` becomes its own
  bundled function, and keeping the shared code in the entrypoint removes any
  cross-file import that could break a deploy.
- The contribution calendar is parsed from `github.com/users/<user>/contributions`
  (the same HTML GitHub renders). `data-date` gives the day, the `tool-tip` text
  gives the count.
- If that markup ever changes, setting `GH_TOKEN` (or `GITHUB_TOKEN`) falls back to
  the GraphQL API automatically. Without it, the service still works.
- Themes and geometry are shared with the artwork committed in
  [`fevnem/fevnem`](https://github.com/fevnem/fevnem), so the live cards match the
  static ones pixel for pixel.

## License

MIT
