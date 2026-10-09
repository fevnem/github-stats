"""The landing page: type a username, preview the cards, copy the embed.

Served at `/`. Everything (styles, script, markup) is inline and self-contained —
no framework, no CDN, no build step, no outbound request except the cards
themselves coming from this same origin. The page is a plain string with no
server-side templating, so the browser URL is the only state.
"""

from __future__ import annotations

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>github-stats — live GitHub contribution cards</title>
<meta name="description" content="Live GitHub contribution stats as embeddable SVG cards. No token, no build step.">
<style>
  :root {
    --bg0:#0a0710; --bg1:#150e26; --panel:#120c22; --fg:#efe9ff; --muted:#a08cc9;
    --line:#2c1d51; --field:#1a1130; --a1:#FF00F6; --a2:#7C3AED; --a3:#22D3EE;
    --shadow:0 24px 60px -30px rgba(124,58,237,.55);
  }
  @media (prefers-color-scheme: light) {
    :root:not([data-theme]) {
      --bg0:#ffffff; --bg1:#f6f3ff; --panel:#ffffff; --fg:#160e2c; --muted:#6f5f9c;
      --line:#e6dcf8; --field:#f4f0ff; --a1:#d600d0; --a2:#6d28d9; --a3:#0891b2;
      --shadow:0 24px 60px -34px rgba(109,40,217,.35);
    }
  }
  :root[data-theme="light"] {
    --bg0:#ffffff; --bg1:#f6f3ff; --panel:#ffffff; --fg:#160e2c; --muted:#6f5f9c;
    --line:#e6dcf8; --field:#f4f0ff; --a1:#d600d0; --a2:#6d28d9; --a3:#0891b2;
    --shadow:0 24px 60px -34px rgba(109,40,217,.35);
  }
  :root[data-theme="dark"] {
    --bg0:#0a0710; --bg1:#150e26; --panel:#120c22; --fg:#efe9ff; --muted:#a08cc9;
    --line:#2c1d51; --field:#1a1130; --a1:#FF00F6; --a2:#7C3AED; --a3:#22D3EE;
    --shadow:0 24px 60px -30px rgba(124,58,237,.55);
  }

  * { box-sizing:border-box; }
  html { color-scheme:dark light; }
  body {
    margin:0; min-height:100vh; color:var(--fg);
    background:
      radial-gradient(900px 480px at 12% -8%, color-mix(in oklab, var(--a2) 26%, transparent), transparent 70%),
      radial-gradient(760px 420px at 92% 4%, color-mix(in oklab, var(--a1) 18%, transparent), transparent 72%),
      linear-gradient(180deg, var(--bg0), var(--bg1));
    font:15px/1.65 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif;
    -webkit-font-smoothing:antialiased;
  }
  .wrap { max-width:940px; margin:0 auto; padding:56px 22px 96px; }
  .mono { font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace; }

  header .kicker {
    font-family:ui-monospace,Menlo,monospace; font-size:11px; letter-spacing:.28em;
    text-transform:uppercase; color:var(--muted);
  }
  h1 { font-size:clamp(30px,5.2vw,44px); line-height:1.1; margin:10px 0 12px; letter-spacing:-.02em; }
  h1 .grad {
    background:linear-gradient(100deg,var(--a1),var(--a2) 55%,var(--a3));
    -webkit-background-clip:text; background-clip:text; color:transparent;
  }
  .lede { color:var(--muted); margin:0; max-width:60ch; }

  .bar {
    display:flex; flex-wrap:wrap; gap:10px; align-items:center;
    margin:30px 0 24px; padding:12px; border:1px solid var(--line);
    border-radius:16px; background:var(--panel); box-shadow:var(--shadow);
  }
  .bar input {
    flex:1 1 220px; min-width:0; padding:12px 14px; border-radius:11px;
    border:1px solid var(--line); background:var(--field); color:var(--fg);
    font:inherit; font-family:ui-monospace,Menlo,monospace;
  }
  .bar input:focus-visible { outline:2px solid var(--a3); outline-offset:1px; }
  button {
    font:inherit; cursor:pointer; border-radius:11px; border:1px solid var(--line);
    background:var(--field); color:var(--fg); padding:11px 15px; transition:.16s ease;
  }
  button:hover { border-color:var(--a2); }
  button:focus-visible { outline:2px solid var(--a3); outline-offset:2px; }
  .primary {
    border:0; color:#fff; font-weight:650; padding:12px 20px;
    background:linear-gradient(100deg,var(--a1),var(--a2));
  }
  .primary:hover { filter:brightness(1.12); }
  .seg { display:inline-flex; border:1px solid var(--line); border-radius:11px; overflow:hidden; }
  .seg button { border:0; border-radius:0; padding:11px 14px; background:transparent; color:var(--muted); }
  .seg button[aria-pressed="true"] { background:var(--field); color:var(--fg); }

  .status { min-height:20px; margin:0 0 18px; font-size:13px; color:var(--muted); }
  .status.err { color:var(--a1); }

  .cards { display:grid; gap:20px; }
  .card {
    padding:18px; border:1px solid var(--line); border-radius:16px;
    background:var(--panel); box-shadow:var(--shadow);
  }
  .card h2 {
    margin:0 0 14px; font-family:ui-monospace,Menlo,monospace; font-size:11px;
    letter-spacing:.2em; text-transform:uppercase; color:var(--muted); font-weight:500;
  }
  .card img { display:block; width:100%; height:auto; min-height:70px; border-radius:10px; }
  .card .row { display:flex; flex-wrap:wrap; gap:8px; margin-top:14px; }
  .card .row button { font-size:12.5px; padding:8px 12px; font-family:ui-monospace,Menlo,monospace; }

  pre {
    margin:0; padding:14px; overflow:auto; border-radius:11px; border:1px solid var(--line);
    background:var(--field); color:var(--muted);
    font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:12px; line-height:1.6;
  }
  section.embed { margin-top:44px; }
  section.embed > h2 { font-size:16px; margin:0 0 6px; }
  section.embed > p { color:var(--muted); margin:0 0 20px; font-size:13.5px; }
  .routes { margin-top:40px; padding:18px; border:1px solid var(--line); border-radius:16px; background:var(--panel); }
  .routes table { width:100%; border-collapse:collapse; font-size:13px; }
  .routes td { padding:7px 0; border-bottom:1px solid var(--line); vertical-align:top; }
  .routes tr:last-child td { border-bottom:0; }
  .routes td:first-child { color:var(--fg); white-space:nowrap; padding-right:18px; }
  .routes td:last-child { color:var(--muted); }
  footer { margin-top:36px; color:var(--muted); font-size:12.5px; }
  footer a { color:var(--muted); }
  code { font-family:ui-monospace,Menlo,monospace; }
</style>
</head>
<body>
<div class="wrap">

  <header>
    <div class="kicker">No token · no build step · stdlib only</div>
    <h1>Live GitHub <span class="grad">contribution cards</span>, as SVG.</h1>
    <p class="lede">Type a username, preview the three cards, copy the snippet into
    your profile README. Each request re-reads GitHub, so the numbers are current —
    nothing to schedule and nothing to keep in sync.</p>
  </header>

  <form class="bar" id="form" autocomplete="off">
    <label for="user" class="mono" style="font-size:11px;letter-spacing:.16em;color:var(--muted)">USER</label>
    <input id="user" name="user" placeholder="octocat" aria-label="GitHub username"
           spellcheck="false" maxlength="39">
    <button class="primary" type="submit">Render</button>
    <div class="seg" role="group" aria-label="Card theme">
      <button type="button" id="t-dark" aria-pressed="true">Dark</button>
      <button type="button" id="t-light" aria-pressed="false">Light</button>
    </div>
  </form>

  <p class="status mono" id="status" aria-live="polite">Waiting for a username…</p>

  <div class="cards">
    <div class="card">
      <h2>Contribution field</h2>
      <img id="img-field" alt="Isometric 3-D field of the last year of contributions">
    </div>
    <div class="card">
      <h2>Streak</h2>
      <img id="img-streak" alt="Totals, current streak and longest streak">
    </div>
    <div class="card">
      <h2>Activity</h2>
      <img id="img-activity" alt="Weekly contribution totals over the last 12 months">
    </div>
  </div>

  <section class="embed">
    <h2>Embed</h2>
    <p>Snippets are generated for this deployment, so the URLs are already correct.</p>
    <div class="cards">
      <div class="card">
        <h2>Contribution field</h2>
        <pre id="pre-field">Render a username to generate the snippet.</pre>
        <div class="row">
          <button type="button" data-copy="field" data-format="html">Copy HTML</button>
          <button type="button" data-copy="field" data-format="md">Copy Markdown</button>
        </div>
      </div>
      <div class="card">
        <h2>Streak &amp; activity</h2>
        <pre id="pre-streak">Render a username to generate the snippet.</pre>
        <div class="row">
          <button type="button" data-copy="streak" data-format="html">Copy streak HTML</button>
          <button type="button" data-copy="activity" data-format="html">Copy activity HTML</button>
        </div>
      </div>
    </div>
  </section>

  <div class="routes">
    <h2 class="mono" style="margin:0 0 12px;font-size:11px;letter-spacing:.2em;color:var(--muted)">ENDPOINTS</h2>
    <table>
      <tr><td class="mono">/</td><td>this page — <code>?user=NAME</code> prefills it</td></tr>
      <tr><td class="mono">/streak?user=NAME</td><td>total contributions, current and longest streak</td></tr>
      <tr><td class="mono">/activity?user=NAME</td><td>weekly totals over the last twelve months</td></tr>
      <tr><td class="mono">/field?user=NAME</td><td>the isometric 3-D contribution field</td></tr>
      <tr><td class="mono">theme=dark|light</td><td>every route accepts it; defaults to dark</td></tr>
    </table>
  </div>

  <footer>
    <p>Cards are cached for ten minutes at the edge and revalidated in the background.
    Errors return a drawn card, so an embed never breaks.</p>
  </footer>
</div>

<script>
(function () {
  var KINDS = ['field', 'streak', 'activity'];
  var state = { user: '', theme: 'dark' };
  var statusEl = document.getElementById('status');

  function say(message, isError) {
    statusEl.textContent = message;
    statusEl.className = 'mono status' + (isError ? ' err' : '');
  }

  function valid(name) { return /^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$/.test(name); }

  function url(kind, user, theme) {
    return '/' + kind + '?user=' + encodeURIComponent(user) + '&theme=' + theme;
  }

  function origin() { return window.location.origin; }

  function picture(kind, user, width) {
    return '<p align="center">\\n' +
      '  <picture>\\n' +
      '    <source media="(prefers-color-scheme: dark)"  srcset="' + origin() + url(kind, user, 'dark') + '">\\n' +
      '    <source media="(prefers-color-scheme: light)" srcset="' + origin() + url(kind, user, 'light') + '">\\n' +
      '    <img ' + (width ? 'width="100%" ' : '') + 'alt="GitHub ' + kind + ' for ' + user + '" src="' + origin() + url(kind, user, 'dark') + '">\\n' +
      '  </picture>\\n' +
      '</p>';
  }

  function render() {
    var user = state.user;
    if (!user) { say('Waiting for a username…', false); return; }
    if (!valid(user)) { say('That is not a valid GitHub username.', true); return; }

    KINDS.forEach(function (kind) {
      document.getElementById('img-' + kind).src = url(kind, user, state.theme);
    });

    var field = picture('field', user, true);
    document.getElementById('pre-field').textContent = field;
    document.getElementById('pre-streak').textContent =
      picture('streak', user, false) + '\\n\\n' + picture('activity', user, true);

    say('Showing ' + user + ' · ' + state.theme + ' theme');
  }

  document.getElementById('form').addEventListener('submit', function (event) {
    event.preventDefault();
    state.user = document.getElementById('user').value.trim();
    var next = new URL(window.location.href);
    if (state.user) { next.searchParams.set('user', state.user); } else { next.searchParams.delete('user'); }
    history.replaceState(null, '', next);
    render();
  });

  function setTheme(theme) {
    state.theme = theme;
    document.documentElement.setAttribute('data-theme', theme);
    document.getElementById('t-dark').setAttribute('aria-pressed', String(theme === 'dark'));
    document.getElementById('t-light').setAttribute('aria-pressed', String(theme === 'light'));
    render();
  }
  document.getElementById('t-dark').addEventListener('click', function () { setTheme('dark'); });
  document.getElementById('t-light').addEventListener('click', function () { setTheme('light'); });

  Array.prototype.forEach.call(document.querySelectorAll('[data-copy]'), function (button) {
    button.addEventListener('click', function () {
      var kind = button.getAttribute('data-copy');
      var format = button.getAttribute('data-format');
      var html = kind === 'streak'
        ? document.getElementById('pre-streak').textContent.split('\\n\\n')[0]
        : document.getElementById('pre-field').textContent;
      var text = (format === 'md') ? '```html\\n' + html + '\\n```' : html;
      copy(text, button);
    });
  });

  function copy(text, button) {
    var done = function () {
      var old = button.textContent;
      button.textContent = 'Copied ✓';
      setTimeout(function () { button.textContent = old; }, 1200);
    };
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(done, function () { fallback(text, done); });
    } else {
      fallback(text, done);
    }
  }

  function fallback(text, done) {
    var area = document.createElement('textarea');
    area.value = text;
    area.setAttribute('readonly', '');
    area.style.position = 'fixed';
    area.style.top = '-1000px';
    document.body.appendChild(area);
    area.select();
    try { document.execCommand('copy'); done(); } catch (error) { say('Copy failed — select the snippet manually.', true); }
    document.body.removeChild(area);
  }

  var prefill = new URL(window.location.href).searchParams.get('user');
  if (prefill) {
    document.getElementById('user').value = prefill;
    state.user = prefill.trim();
  }
  var prefersLight = window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches;
  setTheme(prefersLight ? 'light' : 'dark');
})();
</script>
</body>
</html>
"""


def page() -> str:
    """The landing page as a UTF-8 string."""
    return PAGE
