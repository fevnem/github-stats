"""The landing page.

One self-contained HTML document — no build step, no framework, no CDN. It is the
whole onboarding story: type a username, pick a palette, pick a design, watch the
card update, copy the snippet. The catalogue it renders is read from `palettes` and
`styles`, so the page can never drift from what the service actually supports.
"""

from __future__ import annotations

import json

from github_stats import palettes, styles
from github_stats.config import KINDS, VERSION

DATA = {
    "version": VERSION,
    "kinds": list(KINDS),
    "palettes": [
        {"name": name,
         "label": entry["label"],
         "dark": entry["dark"],
         "light": entry["light"]}
        for name, entry in palettes.PALETTES.items()
    ],
    "styles": [
        {"name": name, "label": styles.STYLE_INFO[name][0], "desc": styles.STYLE_INFO[name][1]}
        for name in styles.STYLE_NAMES
    ],
}

PAGE = r"""<!doctype html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>github-stats — contribution stats as SVG</title>
<meta name="description" content="Live GitHub contribution stats as self-contained SVG cards. Zero dependencies. Runs on a VPS, in Docker or on Vercel.">
<meta name="color-scheme" content="dark light">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' rx='8' fill='%237c3aed'/><path d='M8 21 L13 11 L17 17 L21 13 L24 21' fill='none' stroke='%23fff' stroke-width='2.4' stroke-linecap='round' stroke-linejoin='round'/></svg>">
<style>
*,*::before,*::after{box-sizing:border-box}
:root{
  --bg:#0a0810; --bg2:#0f0c19; --raise:rgba(255,255,255,.035); --raise2:rgba(255,255,255,.06);
  --ink:#f5f2ff; --dim:#a297c4; --faint:#6f678f;
  --line:rgba(255,255,255,.09); --line2:rgba(255,255,255,.16);
  --a1:#ff5cf6; --a2:#8b5cf6; --a3:#2dd4ee;
  --shell:rgba(255,255,255,.02);
  --radius:18px; --radius-sm:12px;
  --shadow:0 30px 70px -28px rgba(0,0,0,.85);
  --mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,monospace;
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,Helvetica,Arial,sans-serif;
}
html[data-theme=light]{
  --bg:#f6f5fb; --bg2:#ffffff; --raise:rgba(20,10,50,.03); --raise2:rgba(20,10,50,.055);
  --ink:#140c28; --dim:#5f5384; --faint:#8b81ab;
  --line:rgba(20,10,50,.10); --line2:rgba(20,10,50,.18);
  --shell:rgba(255,255,255,.7);
  --shadow:0 24px 50px -26px rgba(30,16,70,.35);
}
html{scroll-behavior:smooth}
body{
  margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);
  font-size:16px;line-height:1.6;-webkit-font-smoothing:antialiased;
  background-image:
    radial-gradient(1100px 520px at 12% -12%,color-mix(in srgb,var(--a2) 16%,transparent),transparent 70%),
    radial-gradient(900px 460px at 100% 0%,color-mix(in srgb,var(--a3) 12%,transparent),transparent 65%);
  background-repeat:no-repeat;
}
a{color:inherit;text-decoration:none}
.wrap{max-width:1180px;margin:0 auto;padding:0 24px}
.mono{font-family:var(--mono)}

/* header */
header{
  position:sticky;top:0;z-index:40;backdrop-filter:blur(14px);
  background:color-mix(in srgb,var(--bg) 78%,transparent);
  border-bottom:1px solid var(--line);
}
.bar{display:flex;align-items:center;gap:16px;height:64px}
.brand{display:flex;align-items:center;gap:10px;font-weight:700;letter-spacing:-.01em}
.mark{
  width:30px;height:30px;border-radius:9px;flex:none;
  background:linear-gradient(135deg,var(--a1),var(--a2) 55%,var(--a3));
  box-shadow:0 6px 18px -6px color-mix(in srgb,var(--a1) 60%,transparent);
  display:grid;place-items:center;
}
.mark svg{width:18px;height:18px}
.bar nav{margin-left:auto;display:flex;align-items:center;gap:8px}
.pill{
  display:inline-flex;align-items:center;gap:7px;padding:6px 11px;border-radius:999px;
  border:1px solid var(--line);background:var(--raise);font-size:12.5px;color:var(--dim);
  font-family:var(--mono);transition:.18s;
}
a.pill:hover{border-color:var(--line2);color:var(--ink);background:var(--raise2)}

/* hero */
.hero{padding:70px 0 26px;max-width:780px}
h1{font-size:clamp(34px,5.2vw,54px);line-height:1.05;letter-spacing:-.03em;margin:0 0 18px;font-weight:800}
h1 em{
  font-style:normal;background:linear-gradient(100deg,var(--a1),var(--a2) 45%,var(--a3));
  -webkit-background-clip:text;background-clip:text;color:transparent;
}
.lede{color:var(--dim);font-size:17.5px;margin:0;max-width:62ch}
.tags{display:flex;flex-wrap:wrap;gap:8px;margin-top:22px}
.tag{
  font-family:var(--mono);font-size:11.5px;letter-spacing:.06em;text-transform:uppercase;
  color:var(--dim);border:1px solid var(--line);background:var(--raise);
  padding:5px 10px;border-radius:8px;
}

/* console */
.console{
  margin:38px 0 0;border:1px solid var(--line);border-radius:var(--radius);
  background:linear-gradient(180deg,var(--shell),transparent),var(--bg2);
  box-shadow:var(--shadow);overflow:hidden;
}
.controls{display:flex;flex-wrap:wrap;gap:10px;align-items:center;padding:16px 18px;border-bottom:1px solid var(--line)}
.field{
  display:flex;align-items:center;gap:8px;flex:1 1 220px;min-width:190px;
  border:1px solid var(--line);background:var(--raise);border-radius:var(--radius-sm);
  padding:0 12px;height:44px;transition:.18s;
}
.field:focus-within{border-color:color-mix(in srgb,var(--a2) 60%,var(--line2));box-shadow:0 0 0 3px color-mix(in srgb,var(--a2) 18%,transparent)}
.field span{color:var(--faint);font-family:var(--mono);font-size:13px}
.field input{
  border:0;background:none;outline:none;color:var(--ink);font:inherit;
  width:100%;height:100%;font-family:var(--mono);font-size:14px;
}
.seg{display:flex;gap:4px;padding:4px;border:1px solid var(--line);background:var(--raise);border-radius:var(--radius-sm)}
.seg button{
  border:0;background:none;color:var(--dim);font:inherit;font-size:13px;
  padding:7px 13px;border-radius:9px;cursor:pointer;transition:.16s;font-weight:500;
}
.seg button:hover{color:var(--ink)}
.seg button[aria-pressed=true]{
  background:linear-gradient(135deg,color-mix(in srgb,var(--a1) 26%,transparent),color-mix(in srgb,var(--a2) 30%,transparent));
  color:var(--ink);box-shadow:inset 0 0 0 1px var(--line2);
}
.stage{padding:22px 18px 18px}
.surface{
  border-radius:var(--radius-sm);padding:18px;display:grid;place-items:center;
  border:1px solid var(--line);
  background:
    linear-gradient(45deg,var(--raise) 25%,transparent 25%,transparent 75%,var(--raise) 75%) 0 0/22px 22px,
    linear-gradient(45deg,var(--raise) 25%,transparent 25%,transparent 75%,var(--raise) 75%) 11px 11px/22px 22px,
    var(--bg2);
  min-height:230px;
}
.surface img{max-width:100%;height:auto;display:block}
.meta{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-top:14px}
.hint{color:var(--faint);font-size:13px;font-family:var(--mono)}

/* buttons */
.btn{
  display:inline-flex;align-items:center;gap:8px;border:1px solid var(--line);
  background:var(--raise);color:var(--ink);font:inherit;font-size:13.5px;
  padding:9px 14px;border-radius:10px;cursor:pointer;transition:.18s;font-weight:500;
}
.btn:hover{border-color:var(--line2);background:var(--raise2);transform:translateY(-1px)}
.btn.primary{
  border-color:transparent;color:#fff;
  background:linear-gradient(135deg,var(--a2),var(--a1));
  box-shadow:0 10px 26px -12px color-mix(in srgb,var(--a1) 80%,transparent);
}
.btn.primary:hover{filter:brightness(1.07)}
.btn svg{width:15px;height:15px}

/* sections */
section{padding:56px 0 0}
h2{font-size:22px;margin:0 0 6px;letter-spacing:-.015em}
.sub{color:var(--dim);margin:0 0 22px;font-size:15px;max-width:72ch}

/* palettes */
.swatches{display:flex;flex-wrap:wrap;gap:10px}
.swatch{
  border:1px solid var(--line);background:var(--raise);border-radius:var(--radius-sm);
  padding:9px 13px 9px 9px;display:flex;align-items:center;gap:10px;cursor:pointer;
  transition:.18s;font-size:13px;color:var(--dim);font-weight:500;
}
.swatch:hover{border-color:var(--line2);color:var(--ink);transform:translateY(-1px)}
.swatch[aria-pressed=true]{border-color:color-mix(in srgb,var(--a2) 55%,var(--line2));color:var(--ink);background:var(--raise2)}
.chip{width:34px;height:20px;border-radius:6px;flex:none;box-shadow:inset 0 0 0 1px rgba(255,255,255,.14)}

/* gallery */
.gallery{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:16px}
.tile{
  border:1px solid var(--line);border-radius:var(--radius);background:var(--bg2);
  overflow:hidden;cursor:pointer;transition:.2s;text-align:left;padding:0;color:inherit;font:inherit;
}
.tile:hover{transform:translateY(-3px);border-color:var(--line2);box-shadow:var(--shadow)}
.tile[aria-pressed=true]{border-color:color-mix(in srgb,var(--a2) 60%,var(--line2))}
.tile .shot{padding:14px;border-bottom:1px solid var(--line);display:grid;place-items:center;min-height:150px}
.tile .shot img{max-width:100%;height:auto}
.tile .cap{padding:12px 14px;display:block}
.tile .cap b{display:block;font-size:14.5px;margin-bottom:2px}
.tile .cap i{font-style:normal;color:var(--dim);font-size:13px;line-height:1.45;display:block}
.tile .cap em{font-style:normal;color:var(--faint);font-family:var(--mono);font-size:11.5px;display:block;margin-top:8px}

/* code + tables */
pre{
  margin:0;border:1px solid var(--line);border-radius:var(--radius);background:var(--bg2);
  padding:18px;overflow:auto;font-family:var(--mono);font-size:12.8px;line-height:1.75;color:var(--dim);
}
pre .s{color:color-mix(in srgb,var(--a1) 78%,var(--ink))}
.codehead{display:flex;align-items:center;gap:10px;margin-bottom:10px}
.codehead h3{margin:0;font-size:14px;font-weight:600}
.codehead .btn{margin-left:auto}
.tables{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:22px}
table{width:100%;border-collapse:collapse;font-size:13.5px}
th,td{text-align:left;padding:10px 12px;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--faint);font-family:var(--mono);font-size:11.5px;letter-spacing:.08em;text-transform:uppercase;font-weight:500}
td{color:var(--dim)}
td:first-child{font-family:var(--mono);color:var(--ink);white-space:nowrap}

footer{
  margin-top:70px;border-top:1px solid var(--line);padding:26px 0 60px;
  color:var(--faint);font-size:13px;display:flex;flex-wrap:wrap;gap:12px;align-items:center;
}
.toast{
  position:fixed;left:50%;bottom:28px;transform:translate(-50%,20px);opacity:0;
  background:var(--ink);color:var(--bg);padding:10px 18px;border-radius:999px;
  font-size:13.5px;font-weight:600;transition:.25s;pointer-events:none;z-index:60;
}
.toast[data-on]{opacity:1;transform:translate(-50%,0)}
@media (max-width:640px){
  .hero{padding:44px 0 18px}
  .controls{padding:14px}
  .stage{padding:16px 14px}
}
</style>
</head>
<body>
<header>
  <div class="wrap bar">
    <div class="brand">
      <span class="mark" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M4 17 L9 8 L13 13 L17 10 L20 17"/></svg>
      </span>
      github-stats
    </div>
    <nav>
      <span class="pill mono">v__VERSION__</span>
      <a class="pill" href="#routes">Endpoints</a>
    </nav>
  </div>
</header>

<main class="wrap">
  <div class="hero">
    <h1>Contribution stats,<br>as <em>self-contained SVG</em>.</h1>
    <p class="lede">
      A live stats service you can embed in a README, a site or a dashboard. No chart
      library, no screenshot, no third-party host that quietly dies — just one small
      Python service that draws the card and returns it.
    </p>
    <div class="tags">
      <span class="tag">Zero dependencies</span>
      <span class="tag">VPS · Docker · Vercel</span>
      <span class="tag">__KINDS_COUNT__ card types</span>
      <span class="tag">__STYLE_COUNT__ activity designs</span>
      <span class="tag">__PALETTE_COUNT__ palettes</span>
    </div>
  </div>

  <div class="console">
    <div class="controls">
      <label class="field">
        <span>user/</span>
        <input id="user" value="sindresorhus" spellcheck="false" autocomplete="off" aria-label="GitHub username">
      </label>
      <div class="seg" id="kinds" role="group" aria-label="Card type"></div>
      <div class="seg" id="themes" role="group" aria-label="Theme">
        <button data-theme="dark" aria-pressed="true">Dark</button>
        <button data-theme="light" aria-pressed="false">Light</button>
      </div>
      <div class="seg" id="motions" role="group" aria-label="Motion">
        <button data-motion="1" aria-pressed="true">Animated</button>
        <button data-motion="0" aria-pressed="false">Static</button>
      </div>
    </div>

    <div class="stage">
      <div class="surface"><img id="preview" alt="Selected card preview"></div>
      <div class="meta">
        <button class="btn primary" id="copyurl">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="9" y="9" width="11" height="11" rx="2.5"/><path d="M15 5.5A2.5 2.5 0 0 0 12.5 3h-6A3.5 3.5 0 0 0 3 6.5v6A2.5 2.5 0 0 0 5.5 15"/></svg>
          Copy image URL
        </button>
        <span class="hint" id="dims"></span>
        <span class="hint" id="styleName" style="margin-left:auto"></span>
      </div>
    </div>
  </div>

  <section>
    <h2>Palette</h2>
    <p class="sub">Every card, every design, in any of these colour schemes.</p>
    <div class="swatches" id="palettes"></div>
  </section>

  <section id="designs">
    <h2>Activity designs</h2>
    <p class="sub">The same year of data, drawn five ways. Pick one — the preview and the snippet follow.</p>
    <div class="gallery" id="gallery"></div>
  </section>

  <section id="embed">
    <h2>Embed it</h2>
    <p class="sub">Paste this into a README. The <span class="mono">&lt;picture&gt;</span> follows the
      reader's colour scheme, so the card never sits on the wrong background.</p>
    <div class="codehead"><h3>Markdown</h3><button class="btn" data-copy="snippet">Copy snippet</button></div>
    <pre id="snippet"></pre>
  </section>

  <section id="routes">
    <h2>Endpoints</h2>
    <p class="sub">Three routes, one shape. Swap <span class="mono">theme</span>,
      <span class="mono">palette</span>, <span class="mono">style</span> or
      <span class="mono">motion</span> to change the result.</p>
    <div class="tables">
      <table>
        <thead><tr><th>Route</th><th>Draws</th></tr></thead>
        <tbody>
          <tr><td>/field</td><td>The year as an isometric field of tiles</td></tr>
          <tr><td>/streak</td><td>Totals, current streak, longest streak</td></tr>
          <tr><td>/activity</td><td>Weekly totals — five designs, see above</td></tr>
        </tbody>
      </table>
      <table>
        <thead><tr><th>Parameter</th><th>Values</th></tr></thead>
        <tbody>
          <tr><td>user</td><td>Required. Any GitHub username.</td></tr>
          <tr><td>theme</td><td><span class="mono">dark</span> (default) or <span class="mono">light</span></td></tr>
          <tr><td>palette</td><td id="tp"></td></tr>
          <tr><td>style</td><td id="ts"></td></tr>
          <tr><td>motion</td><td><span class="mono">1</span> (default) or <span class="mono">0</span> to freeze the entrance animation</td></tr>
        </tbody>
      </table>
    </div>
  </section>

  <footer>
    <span>No account, no token, no tracking. Reads the public contribution calendar.</span>
    <span class="mono" style="margin-left:auto">MIT</span>
  </footer>
</main>

<div class="toast" id="toast">Copied</div>

<script>
const DATA = /*__DATA__*/;
const SIZES = {field:[900,400], streak:[520,200], activity:[880,250]};
const state = {user:"sindresorhus", theme:"dark", palette:"aurora", kind:"activity", style:"aurora", motion:"1"};
const $ = (id) => document.getElementById(id);

/* Escape anything a visitor typed before it goes back into markup. */
function h(value) {
  return String(value).replace(/[&<>"']/g, (c) =>
    ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
}

function query(extra) {
  return new URLSearchParams(Object.assign(
    {user: state.user, theme: state.theme, palette: state.palette,
     style: state.style, motion: state.motion}, extra)).toString();
}
function url(kind, extra) { return location.origin + "/" + (kind || state.kind) + "?" + query(extra); }

let toastTimer;
function toast(text) {
  const el = $("toast");
  el.textContent = text; el.setAttribute("data-on", "");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.removeAttribute("data-on"), 1600);
}
function copy(text, what) {
  const done = () => toast(what + " copied");
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(text).then(done, () => { fallback(text); done(); });
  } else { fallback(text); done(); }
}
function fallback(text) {
  const area = document.createElement("textarea");
  area.value = text; area.setAttribute("readonly", "");
  area.style.position = "fixed"; area.style.top = "-1000px";
  document.body.appendChild(area); area.select();
  try { document.execCommand("copy"); } catch (error) { toast("Copy failed"); }
  document.body.removeChild(area);
}

/* ---------- build the controls ---------- */
const startKind = DATA.kinds.indexOf("activity");
$("kinds").innerHTML = DATA.kinds.map((kind, index) =>
  `<button data-kind="${h(kind)}" aria-pressed="${index === startKind}">${h(kind[0].toUpperCase() + kind.slice(1))}</button>`
).join("");

$("palettes").innerHTML = DATA.palettes.map((p) =>
  `<button class="swatch" data-palette="${h(p.name)}" aria-pressed="${p.name === state.palette}">
     <span class="chip" style="background:linear-gradient(135deg,${h(p.dark[0])},${h(p.dark[1])} 55%,${h(p.dark[2])})"></span>${h(p.label)}
   </button>`
).join("");

$("gallery").innerHTML = DATA.styles.map((s) =>
  `<button class="tile" data-style="${h(s.name)}" aria-pressed="${s.name === state.style}">
     <span class="shot"><img data-style-img="${h(s.name)}" loading="lazy" alt="${h(s.label)} design"></span>
     <span class="cap"><b>${h(s.label)}</b><i>${h(s.desc)}</i><em>style=${h(s.name)}</em></span>
   </button>`
).join("");

$("tp").innerHTML = DATA.palettes.map((p) => `<span class="mono">${h(p.name)}</span>`).join(", ");
$("ts").innerHTML = DATA.styles.map((s) => `<span class="mono">${h(s.name)}</span>`).join(", ");

/* ---------- render ---------- */
function paint() {
  document.documentElement.setAttribute("data-theme", state.theme);
  const press = (selector, key, value) => document.querySelectorAll(selector)
    .forEach((b) => b.setAttribute("aria-pressed", String(b.dataset[key] === value)));
  press("#themes button", "theme", state.theme);
  press("#kinds button", "kind", state.kind);
  press("#motions button", "motion", state.motion);
  press("[data-palette]", "palette", state.palette);
  press("[data-style]", "style", state.style);

  DATA.palettes.forEach((p) => {
    const chip = document.querySelector(`[data-palette="${p.name}"] .chip`);
    const c = p[state.theme];
    if (chip && c) chip.style.background = `linear-gradient(135deg,${c[0]},${c[1]} 55%,${c[2]})`;
  });

  $("preview").src = url();
  const size = SIZES[state.kind] || SIZES.activity;
  $("dims").textContent = `${size[0]}×${size[1]} · ${state.kind}.svg`;
  $("styleName").textContent = state.kind === "activity"
    ? (DATA.styles.find((s) => s.name === state.style) || {}).label : "";

  document.querySelectorAll("[data-style-img]").forEach((img) =>
    img.src = url("activity", {style: img.dataset.styleImg}));

  const dark = url(null, {theme: "dark"});
  const light = url(null, {theme: "light"});
  $("snippet").innerHTML =
`&lt;picture&gt;
  &lt;source media=<span class="s">"(prefers-color-scheme: dark)"</span> srcset=<span class="s">"${h(dark)}"</span>&gt;
  &lt;img alt=<span class="s">"Contribution activity for ${h(state.user)}"</span> src=<span class="s">"${h(light)}"</span>&gt;
&lt;/picture&gt;`;
}

$("user").addEventListener("input", (event) => {
  state.user = event.target.value.trim() || "sindresorhus";
  paint();
});
$("kinds").addEventListener("click", (event) => {
  const kind = event.target.closest("[data-kind]");
  if (kind) { state.kind = kind.dataset.kind; $("designs").style.display = kind.dataset.kind === "activity" ? "" : "none"; paint(); }
});
$("themes").addEventListener("click", (event) => {
  const theme = event.target.closest("[data-theme]");
  if (theme) { state.theme = theme.dataset.theme; paint(); }
});
$("motions").addEventListener("click", (event) => {
  const motion = event.target.closest("[data-motion]");
  if (motion) { state.motion = motion.dataset.motion; paint(); }
});
$("palettes").addEventListener("click", (event) => {
  const swatch = event.target.closest("[data-palette]");
  if (swatch) { state.palette = swatch.dataset.palette; paint(); }
});
$("gallery").addEventListener("click", (event) => {
  const tile = event.target.closest("[data-style]");
  if (tile) { state.style = tile.dataset.style; state.kind = "activity"; $("designs").style.display = ""; paint(); }
});
$("copyurl").addEventListener("click", () => copy(url(), "Image URL"));
document.querySelector('[data-copy="snippet"]').addEventListener("click", () =>
  copy($("snippet").textContent, "Snippet"));

// The whole view is a URL — ?user= &theme= &palette= &style= &kind= &motion= — so a
// configured preview can be linked or bookmarked.
const link = new URL(window.location.href).searchParams;
const pick = (key, allowed) => {
  const value = link.get(key);
  return value && allowed.includes(value) ? value : null;
};

state.user = (link.get("user") || state.user).trim() || state.user;
$("user").value = state.user;
state.theme = pick("theme", ["dark", "light"])
  || ((window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches)
      ? "light" : "dark");
state.palette = pick("palette", DATA.palettes.map((p) => p.name)) || state.palette;
state.style = pick("style", DATA.styles.map((s) => s.name)) || state.style;
state.kind = pick("kind", DATA.kinds) || state.kind;
state.motion = pick("motion", ["0", "1"]) || state.motion;
if (state.kind !== "activity") $("designs").style.display = "none";

paint();
</script>
</body>
</html>
"""


def page() -> str:
    """The landing page, with the catalogue and the version injected."""
    return (PAGE
            .replace("/*__DATA__*/", json.dumps(DATA, separators=(",", ":")))
            .replace("__VERSION__", VERSION)
            .replace("__KINDS_COUNT__", str(len(KINDS)))
            .replace("__STYLE_COUNT__", str(len(styles.STYLE_NAMES)))
            .replace("__PALETTE_COUNT__", str(len(palettes.PALETTES))))
