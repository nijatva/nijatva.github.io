#!/usr/bin/env python3
"""Build every Nijatva page from apps_data.py. No framework, no build step at runtime."""
import pathlib, sys, html, json
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from apps_data import (APPS, SUITE, ECOSYSTEM, FOUNDATION, PHASES, STATUS_LABEL, STATUS_CLASS,
                       SIZE_LABEL, GH, GH_USER, SITE, EMAIL, UPDATED)

ASSET_V = "6"  # bump to force browsers past a cached stylesheet
ROOT = pathlib.Path(__file__).parent.parent
E = html.escape


THEME_SCRIPT = """
<script>
/* The only script on this site. It remembers your theme and accent in this
   browser and sets two attributes on <html>. No network requests, no cookies. */
(function () {
  var d = document.documentElement;
  var mq = window.matchMedia("(prefers-color-scheme: dark)");
  function read(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function write(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  function sync() {
    var t = d.getAttribute("data-theme") || "system";
    d.setAttribute("data-scheme", t === "system" ? (mq.matches ? "dark" : "light") : t);
  }
  var theme = read("nj-theme"), accent = read("nj-accent");
  if (theme) d.setAttribute("data-theme", theme);
  if (accent) d.setAttribute("data-accent", accent);
  sync();
  if (mq.addEventListener) mq.addEventListener("change", sync);
  document.addEventListener("change", function (e) {
    var el = e.target;
    if (el.name === "theme") { d.setAttribute("data-theme", el.value); write("nj-theme", el.value); sync(); }
    if (el.name === "accent") { d.setAttribute("data-accent", el.value); write("nj-accent", el.value); }
  });
  document.addEventListener("DOMContentLoaded", function () {
    var t = d.getAttribute("data-theme") || "system";
    var a = d.getAttribute("data-accent") || "saffron";
    var rt = document.querySelector('input[name="theme"][value="' + t + '"]');
    var ra = document.querySelector('input[name="accent"][value="' + a + '"]');
    if (rt) rt.checked = true;
    if (ra) ra.checked = true;
  });
})();
</script>
"""

APPEARANCE = """
    <details class="appearance">
      <summary aria-label="Appearance settings">
        <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="3.2"/><path d="M12 3.5v2.2M12 18.3v2.2M3.5 12h2.2M18.3 12h2.2M6 6l1.6 1.6M16.4 16.4L18 18M18 6l-1.6 1.6M7.6 16.4L6 18"/></svg>
        <span>Appearance</span>
      </summary>
      <div class="appearance-panel">
        <p class="eyebrow">Appearance</p>
        <fieldset>
          <legend>Theme</legend>
          <div class="pills">
            <label class="pill"><input type="radio" name="theme" value="system"><span>System</span></label>
            <label class="pill"><input type="radio" name="theme" value="dark"><span>Dark</span></label>
            <label class="pill"><input type="radio" name="theme" value="light"><span>Light</span></label>
            <label class="pill"><input type="radio" name="theme" value="black"><span>Black</span></label>
          </div>
        </fieldset>
        <fieldset>
          <legend>Accent colour</legend>
          <div class="pills">
            <label class="pill" data-swatch="green"><input type="radio" name="accent" value="green"><span>Green</span></label>
            <label class="pill" data-swatch="saffron"><input type="radio" name="accent" value="saffron"><span>Saffron</span></label>
            <label class="pill" data-swatch="indigo"><input type="radio" name="accent" value="indigo"><span>Indigo</span></label>
          </div>
        </fieldset>
        <p class="appearance-note">Saved in this browser only. Nothing about your choice leaves this device.</p>
      </div>
    </details>
"""

NAV = [("apps.html", "Apps"), ("architecture.html", "Architecture"),
       ("index.html#principles", "Principles"), ("developer.html", "Developer"),
       (GH, "GitHub")]


def head(title, desc, canonical, root="", image=True, extra=""):
    og_img = ('<meta property="og:image" content="%s/og.png">\n'
              '<meta property="og:image:width" content="1200">\n'
              '<meta property="og:image:height" content="630">\n'
              '<meta name="twitter:card" content="summary_large_image">\n'
              '<meta name="twitter:image" content="%s/og.png">\n' % (SITE, SITE)) if image else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<meta name="theme-color" content="#1b1f45" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0c0e1c" media="(prefers-color-scheme: dark)">
<link rel="icon" href="{root}assets/favicon.svg" type="image/svg+xml">
{THEME_SCRIPT}<link rel="stylesheet" href="{root}assets/tokens.css?v={ASSET_V}">
<link rel="stylesheet" href="{root}assets/site.css?v={ASSET_V}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Nijatva">
<meta property="og:locale" content="en_IN">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{canonical}">
{og_img}{extra}</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
"""


def header(root="", current=""):
    links = []
    for href, label in NAV:
        abs_href = href if href.startswith("http") else root + href
        cur = ' aria-current="page"' if href == current else ""
        links.append(f'      <a href="{abs_href}"{cur}>{E(label)}</a>')
    links = "\n".join(links)
    return f"""
<header class="site-header">
  <div class="container header-inner">
    <a class="brand" href="{root}index.html" aria-label="Nijatva home">
      <img src="{root}assets/logo.svg" alt="" width="34" height="34">
      <span>Nijatva</span>
    </a>
    <nav class="nav" aria-label="Primary">
{links}
    </nav>
    <a class="header-search" href="{root}search.html" aria-label="Search the site">
      <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="6.4"/><path d="M15.6 15.6L21 21"/></svg>
    </a>
{APPEARANCE}    <details class="nav-menu">
      <summary><span class="menu-icon" aria-hidden="true"></span><span>Menu</span></summary>
      <nav class="nav-menu-panel" aria-label="Mobile">
{links}
      </nav>
    </details>
  </div>
</header>
"""


def footer(root=""):
    return f"""
<footer class="site-footer">
  <div class="container">
    <div class="footer-grid">
      <div>
        <div class="footer-brand">
          <img src="{root}assets/logo.svg" alt="" width="32" height="32">
          <span>Nijatva</span>
        </div>
        <p>Small, single-purpose Android apps with no Google Play Services, no accounts, no ads and no analytics. Built in India.</p>
        <a class="dev-card" href="{root}developer.html">
          <div class="dev-avatar" aria-hidden="true">VD</div>
          <div>
            <p class="dev-name">Vasudev Dangaya</p>
            <p class="dev-role">Independent developer &middot; India</p>
            <span class="dev-link">Developer profile</span>
          </div>
        </a>
      </div>
      <div>
        <h2>Apps</h2>
        <div class="footer-links">
          <a href="{root}apps.html">All 24 apps</a>
          <a href="{root}apps.html#phase-1">Phase 1 &middot; Small apps</a>
          <a href="{root}apps.html#phase-4">Phase 4 &middot; Flagship</a>
        </div>
      </div>
      <div>
        <h2>Project</h2>
        <div class="footer-links">
          <a href="{root}architecture.html">Architecture</a>
          <a href="{root}architecture.html#roadmap">Real status</a>
          <a href="{root}developer.html">Developer</a>
          <a href="{GH}">Source on GitHub</a>
        </div>
      </div>
      <div>
        <h2>Contact</h2>
        <div class="footer-links">
          <a href="mailto:{EMAIL}">{EMAIL}</a>
          <a href="{root}index.html#why">Why "Nijatva"</a>
        </div>
      </div>
    </div>
    <div class="footer-legal">
      <span>Status as of {UPDATED}. Nijatva &middot; India</span>
      <span>No cookies, no analytics, no external fonts, no third-party requests.</span>
    </div>
  </div>
</footer>
</body>
</html>
"""


def app_card(app, root="", media_note=False):
    status = STATUS_LABEL[app["status"]]
    cls = STATUS_CLASS[app["status"]]
    note = ""
    if app["status"] != "planned" and app.get("note"):
        note = f'\n        <p class="app-card-note">{E(app["note"])}</p>'
    return f"""      <article class="card app-card">
        <div class="app-card-preview">
          <img src="{root}assets/icons/{app['slug']}.svg" alt="" width="76" height="76" loading="lazy">
        </div>
        <div class="app-card-body">
          <div class="app-card-header">
            <div class="app-card-title-block">
              <h3>{E(app["name"])}</h3>
              <div class="badge-row">
                <span class="badge">{SIZE_LABEL[app["size"]]}</span>
                <span class="status-badge {cls}">{status}</span>
              </div>
            </div>
          </div>
          <p>{E(app["summary"])}</p>{note}
          <div class="app-card-actions">
            <a class="button primary" href="{root}apps/{app['slug']}.html">View app</a>
          </div>
        </div>
      </article>"""


# ---------------------------------------------------------------- index
def build_index():
    wall = ["notes", "gallery", "browser", "calendar", "camera", "music",
            "files", "clock", "keyboard"]
    by = {a["slug"]: a for a in APPS}
    tiles = "\n".join(
        f'        <div class="wall-tile"><img src="assets/icons/{s}.svg" alt="" width="46" height="46" loading="lazy">'
        f'<span>{E(by[s]["name"])}</span></div>' for s in wall)

    trust = [
        ("shield", "No Google Play Services",
         "Built for AOSP without GMS, so it runs on de-Googled Android and on BharOS."),
        ("user", "No accounts", "There is nothing to sign up for. Everything stays in device storage."),
        ("eye", "No ads or analytics", "No tracking SDK is linked in. Not disabled, not opt-out. Absent."),
        ("flag", "Made in India", "Indian languages and Indian networks as the first target, not an afterthought."),
    ]
    icons = {
        "shield": '<path d="M12 3l7 3v6c0 4.2-2.9 7.6-7 9-4.1-1.4-7-4.8-7-9V6z"/><path d="M9 12l2 2 4-4"/>',
        "user": '<circle cx="12" cy="8" r="3.4"/><path d="M5 20a7 7 0 0 1 14 0"/>',
        "eye": '<path d="M2 12s3.6-6 10-6 10 6 10 6-3.6 6-10 6-10-6-10-6z"/><circle cx="12" cy="12" r="2.6"/>',
        "flag": '<path d="M6 21V4"/><path d="M6 4h12l-2.5 4L18 12H6"/>',
    }
    metrics = "\n".join(
        f'        <div class="metric"><svg viewBox="0 0 24 24" aria-hidden="true">{icons[i]}</svg>'
        f'<strong>{E(t)}</strong><span>{E(b)}</span></div>' for i, t, b in trust)

    featured = "\n".join(app_card(by[s]) for s in ("browser", "camera", "photos", "appstore"))
    phases = "\n".join(
        f"""      <article class="card">
        <div class="badge-row"><span class="badge">Phase {n}</span><span class="badge">{len([a for a in SUITE if a['phase'] == n])} apps</span></div>
        <h3>{E(PHASES[n][0])}</h3>
        <p>{E(PHASES[n][1])}</p>
        <p class="app-card-note">{E(", ".join(a["name"] for a in SUITE if a["phase"] == n))}</p>
        <div class="app-card-actions"><a class="button subtle" href="apps.html#phase-{n}">Open phase {n}</a></div>
      </article>""" for n in (1, 2, 3, 4))

    principles = "\n".join(
        f'        <div class="principle"><h3>{E(t)}</h3><p>{E(b)}</p></div>' for _, t, b in trust)

    body = f"""{header("", "")}
<main id="main">

  <section class="hero">
    <div class="container hero-grid">
      <div class="hero-copy">
        <p class="eyebrow">Made in India</p>
        <h1 class="hero-title">Nijatva</h1>
        <p class="lead lede-narrow">Twenty-four small, single-purpose Android apps for the things a phone already does. Each one does a job and then gets out of the way. No account, no ads, no tracker, no Google Play Services.</p>
        <div class="actions">
          <a class="button primary" href="apps.html">Explore the 24 apps</a>
          <a class="button" href="architecture.html">How it is built</a>
        </div>
      </div>
      <div class="icon-wall" aria-label="A sample of the Nijatva app set">
{tiles}
      </div>
      <div class="hero-metrics" aria-label="What every app guarantees">
{metrics}
      </div>
    </div>
  </section>

  <section class="section section-band" id="available">
    <div class="container">
      <div class="section-heading">
        <div>
          <p class="eyebrow">Available now</p>
          <h2 class="section-title">Eight apps ship releases</h2>
        </div>
        <div>
          <p class="lead">Eight of the twenty-four have a downloadable build, and four more ship beside them — Photos, Video Player, Drive and Browser Mini X. The Appstore ties them together.</p>
          <a class="section-link" href="apps.html">View the full list</a>
        </div>
      </div>
      <div class="grid two">
{featured}
      </div>
    </div>
  </section>

  <section class="section" id="suite">
    <div class="container">
      <div class="section-heading">
        <div>
          <p class="eyebrow">The suite</p>
          <h2 class="section-title">24 apps, built in four phases</h2>
        </div>
        <div>
          <p class="lead">Foundation first, then the small apps, then the phone roles, then the flagship builds. Nothing ships until the shared pieces exist.</p>
          <a class="section-link" href="apps.html">Browse all apps</a>
        </div>
      </div>
      <div class="grid two">
{phases}
      </div>
    </div>
  </section>

  <section class="section section-band" id="principles">
    <div class="container">
      <div class="section-heading">
        <div>
          <p class="eyebrow">Principles</p>
          <h2 class="section-title">Four rules we do not bend</h2>
        </div>
        <div><p class="lead">Every app, without exception. If an app cannot meet all four, it does not ship.</p></div>
      </div>
      <div class="principles">
{principles}
      </div>
    </div>
  </section>

  <section class="section" id="install">
    <div class="container grid three">
      <article class="panel">
        <p class="eyebrow">Install</p>
        <h2>Our own store</h2>
        <p>Releases are published on GitHub with the APK attached, and the Nijatva Appstore lists them, verifies every download against a SHA-256 hash and installs it. No Play Store, no account.</p>
        <div class="text-link-list"><a href="{GH}/nijatva-browser/releases/latest">Latest Browser release</a></div>
      </article>
      <article class="panel">
        <p class="eyebrow">Status</p>
        <h2>What exists today</h2>
        <p>Eight apps have releases, one more has a repository without one, and fifteen are planned. The roadmap page says so in a table rather than in adjectives.</p>
        <div class="text-link-list"><a href="architecture.html#roadmap">Real status</a></div>
      </article>
      <article class="panel">
        <p class="eyebrow">Contact</p>
        <h2>Source and questions</h2>
        <p>The source is public, including the repositories that are still only a README. Write to us for anything else.</p>
        <div class="text-link-list">
          <a href="{GH}">GitHub</a>
          <a href="mailto:{EMAIL}">{EMAIL}</a>
        </div>
      </article>
    </div>
  </section>

  <section class="section" id="why" style="border-bottom:0">
    <div class="container" style="max-width:760px">
      <p class="eyebrow">The name</p>
      <h2 class="section-title">Why "Nijatva"?</h2>
      <p class="lead">In Sanskrit, <em>nijatva</em> means own-ness &mdash; the state of being your own. It is a good word for software that does not ask for your data in exchange for doing its job.</p>
      <p class="lead">Nijatva is built in India, independently. The Browser ships releases today; the Camera is being built in the open; the rest of the twenty-four are planned, and this site says which is which.</p>
      <div class="actions"><a class="button primary" href="apps.html">See the apps</a>
      <a class="button" href="mailto:{EMAIL}">Write to us</a></div>
    </div>
  </section>

</main>
{footer("")}"""
    return head("Nijatva — 24 Android apps with no Google Play Services",
                "Nijatva is a suite of 24 small, single-purpose Android apps built without Google Play Services, accounts, ads or analytics. Made in India.",
                SITE + "/") + body


# ---------------------------------------------------------------- apps directory
def build_apps():
    chips = "\n".join(
        f'          <a class="chip-link" href="#phase-{n}">Phase {n} &middot; {E(PHASES[n][0])}</a>'
        for n in (1, 2, 3, 4))

    sections = []
    for n in (1, 2, 3, 4):
        group = [a for a in APPS if a["phase"] == n]
        cards = "\n".join(app_card(a) for a in group)
        sections.append(f"""  <section class="section" id="phase-{n}">
    <div class="container">
      <div class="section-heading">
        <div>
          <p class="eyebrow">Phase {n}</p>
          <h2 class="section-title">{E(PHASES[n][0])}</h2>
        </div>
        <div><p class="lead">{E(PHASES[n][1])}</p></div>
      </div>
      <div class="grid three">
{cards}
      </div>
    </div>
  </section>""")
    eco_cards = "\n".join(app_card(a) for a in ECOSYSTEM)
    ecosystem = f"""  <section class="section section-band" id="ecosystem">
    <div class="container">
      <div class="section-heading">
        <div>
          <p class="eyebrow">Ecosystem</p>
          <h2 class="section-title">Not one of the 24</h2>
        </div>
        <div><p class="lead">Seven projects that sit beside the plan: the store that ships the suite, a gallery with on-device machine learning, a player that runs on five platforms, a file vault and a browser that installs alongside the main one.</p></div>
      </div>
      <div class="grid three">
{eco_cards}
      </div>
    </div>
  </section>

"""
    sections = "\n\n".join(sections)

    foundation = "\n".join(
        f"""      <article class="card">
        <h3><code>{E(name)}</code></h3>
        <div class="badge-row"><span class="badge">{E(role)}</span><span class="status-badge planned">README only</span></div>
        <p>{E(desc)}</p>
        <div class="app-card-actions"><a class="button subtle" href="{GH}/{name}">Repository</a></div>
      </article>""" for name, role, desc in FOUNDATION)

    body = f"""{header("", "apps.html")}
<main id="main">

  <section class="section" style="border-bottom:1px solid var(--line)">
    <div class="container">
      <div class="app-hero-grid" style="align-items:start">
        <div>
          <p class="eyebrow">Apps</p>
          <h1 class="page-title">The Nijatva suite</h1>
          <p class="lead">Twenty-four Android apps for photos, files, calls, messages, music, notes, documents, the keyboard and the home screen. Seven have releases today, two have repositories, fifteen are planned, and every card says which.</p>
          <div class="actions" style="margin-top:22px">
{chips}
          </div>
        </div>
        <aside class="panel status-key" aria-labelledby="status-key-title">
          <h2 id="status-key-title">Release status</h2>
          <dl>
            <div>
              <dt><span class="status-badge shipped">Shipped</span></dt>
              <dd>Public releases you can download and install.</dd>
            </div>
            <div>
              <dt><span class="status-badge progress">In progress</span></dt>
              <dd>Public code and tags, no release yet.</dd>
            </div>
            <div>
              <dt><span class="status-badge planned">Planned</span></dt>
              <dd>Specified and scoped. No repository yet.</dd>
            </div>
          </dl>
          <a href="architecture.html#roadmap">Status as of {UPDATED}</a>
        </aside>
      </div>
    </div>
  </section>

{sections}

{ecosystem}  <section class="section section-band" id="foundation">
    <div class="container">
      <div class="section-heading">
        <div>
          <p class="eyebrow">Foundation</p>
          <h2 class="section-title">The shared pieces</h2>
        </div>
        <div><p class="lead">Four repositories that every app is built on. All four exist today and contain a README only &mdash; the code is the next step, and it comes before the apps.</p></div>
      </div>
      <div class="grid two">
{foundation}
      </div>
    </div>
  </section>

</main>
{footer("")}"""
    return head("Apps — Nijatva", "All 24 Nijatva Android apps by phase, with honest release status: two have code today, twenty-two are planned.",
                SITE + "/apps.html") + body


# ---------------------------------------------------------------- app detail
ICON_PLAY = ('<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/>'
             '<path d="M10 8.5l6 3.5-6 3.5z"/></svg>')
ICON_DOWNLOAD = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 4v10"/>'
                 '<path d="M8 11l4 4 4-4"/><path d="M5 19h14"/></svg>')
ICON_LINK = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M10.6 13.4a3.9 3.9 0 0 0 5.5 0l2.2-2.2a3.9 3.9 0 0 0-5.5-5.5l-1.1 1.1"/>'
             '<path d="M13.4 10.6a3.9 3.9 0 0 0-5.5 0l-2.2 2.2a3.9 3.9 0 0 0 5.5 5.5l1.1-1.1"/></svg>')


def build_app_pages():
    outdir = ROOT / "apps"
    outdir.mkdir(exist_ok=True)
    written = []
    for i, app in enumerate(APPS):
        prev_app = APPS[i - 1] if i > 0 else None
        next_app = APPS[i + 1] if i < len(APPS) - 1 else None
        status, cls = STATUS_LABEL[app["status"]], STATUS_CLASS[app["status"]]

        repo_name = app.get("repo", "nijatva-" + app["slug"])

        def local_href(target):
            # A page can live in this repository (a folder) or in the app's own
            # repository, served from its GitHub Pages site (an absolute URL).
            return target if target.startswith("http") else "../" + target

        web_href = local_href

        actions = [f'<a class="button" href="../apps.html">All apps</a>']
        if app["status"] != "planned" and app.get("source_public", True):
            actions.insert(0, f'<a class="button" href="{GH}/{repo_name}">Source on GitHub</a>')
        if app.get("website"):
            actions.insert(0, f'<a class="button" href="{local_href(app["website"])}">{ICON_LINK}Website</a>')
        if app["status"] == "shipped":
            actions.insert(0, f'<a class="button primary" href="{GH}/{repo_name}/releases/latest">{ICON_DOWNLOAD}Download</a>')
        if app.get("web"):
            actions.insert(0, f'<a class="button primary" href="{web_href(app["web"])}">{ICON_PLAY}Open web app</a>')
        actions = "\n          ".join(actions)

        features = "\n".join(f'        <li>{E(f)}</li>' for f in app["features"])
        if app.get("source_public", True) and app["status"] != "planned":
            repo_row = f'<dd><a href="{GH}/{repo_name}">{E(repo_name)}</a></dd>'
        elif app["status"] != "planned":
            repo_row = f'<dd>{E(repo_name)} <span style="font-weight:400;color:var(--muted)">(private)</span></dd>'
        else:
            repo_row = f'<dd>{E(repo_name)} <span style="font-weight:400;color:var(--muted)">(planned)</span></dd>'
        web_row = (f'\n        <div><dt>Web app</dt><dd><a href="{web_href(app["web"])}">Open in browser</a></dd></div>'
                   if app.get("web") else "")
        note = f'\n      <p class="note">{E(app["note"])}</p>' if app.get("note") else ""

        pager = ""
        if prev_app or next_app:
            left = (f'<a class="prev" href="{prev_app["slug"]}.html"><span>Previous</span><strong>{E(prev_app["name"])}</strong></a>'
                    if prev_app else "<div></div>")
            right = (f'<a class="next" href="{next_app["slug"]}.html"><span>Next</span><strong>{E(next_app["name"])}</strong></a>'
                     if next_app else "<div></div>")
            pager = f'\n  <div class="container pager">\n    {left}\n    {right}\n  </div>'

        store_note = ("This is the store itself: every other app on this site installs through it. "
                      "No Google Play Services, no account, no ads, no analytics."
                      if not app.get("suite", True) else
                      "Like every app in the suite: no Google Play Services, no account, no ads, no analytics. Distribution is an APK, never a store.")
        body = f"""{header("../", "")}
<main id="main">
  <div class="container breadcrumb"><a href="../apps.html">Apps</a> &nbsp;/&nbsp; {E(app["name"])}</div>

  <section class="app-hero">
    <div class="container app-hero-grid">
      <div>
        <div class="app-hero-head">
          <img src="../assets/icons/{app["slug"]}.svg" alt="" width="84" height="84">
          <div>
            <h1>{E(app["name"])}</h1>
            <div class="badge-row">
              <span class="status-badge {cls}">{status}</span>
              <span class="badge">{SIZE_LABEL[app["size"]]}</span>
              <span class="badge">{("Ecosystem" if app["phase"] == 0 else "Phase %d" % app["phase"])}</span>
            </div>
          </div>
        </div>
        <p class="lead">{E(app["summary"])}</p>
        <div class="actions">
          {actions}
        </div>{note}
      </div>
      <dl class="app-meta">
        <div><dt>Status</dt><dd>{status}</dd></div>
        <div><dt>{"Part of" if app["phase"] == 0 else "Phase"}</dt><dd>{(E("The ecosystem, not the 24")) if app["phase"] == 0 else (str(app["phase"]) + " &middot; " + E(PHASES[app["phase"]][0]))}</dd></div>
        <div><dt>Build size</dt><dd>{SIZE_LABEL[app["size"]]}</dd></div>
        <div><dt>Repository</dt>{repo_row}</div>{web_row}
        <div><dt>Store</dt><dd>None &middot; APK only</dd></div>
      </dl>
    </div>
  </section>

  <section class="section" style="border-bottom:0">
    <div class="container" style="max-width:760px">
      <p class="eyebrow">What it does</p>
      <h2 class="section-title">{"Shipped features" if app["status"] == "shipped" else ("Features in the build" if app["status"] == "in-progress" else "Planned features")}</h2>
      <ul class="feature-list">
{features}
      </ul>
      <p class="lead" style="margin-top:28px;font-size:15.5px">{store_note}</p>
    </div>
  </section>
{pager}
</main>
{footer("../")}"""
        desc = f'{app["name"]} — {app["summary"]}'
        page = head(f'{app["name"]} — Nijatva', desc, f'{SITE}/apps/{app["slug"]}.html',
                    root="../", image=True) + body
        (outdir / f'{app["slug"]}.html').write_text(page)
        written.append(app["slug"])
    return written


# ---------------------------------------------------------------- architecture
def build_architecture():
    layers = f"""      <div class="layers">
        <div class="layer">
          <b>F4 &middot; nijatva-suite</b>
          <small>App index, release downloads, self-hosted F-Droid style repository</small>
        </div>
        <div class="connector"></div>
        <div class="row3">
          <div class="layer mid"><b>F1 &middot; nijatva-core</b><code>Compose UI, SAF, backup</code><small>Design system and shared helpers</small></div>
          <div class="layer mid"><b>F2 &middot; no-gms-check</b><code>Gradle plugin, CI action</code><small>Fails the build on any GMS artefact</small></div>
          <div class="layer mid"><b>F3 &middot; nijatva-design</b><code>Icons, templates</code><small>Keeps 24 repos looking like one suite</small></div>
        </div>
        <div class="connector"></div>
        <div class="row3">
          <div class="layer mid"><b>Phase 1 &middot; 5</b><small>Calc, Clock, Notes, QR, Files</small></div>
          <div class="layer mid"><b>Phase 2 and 3 &middot; 15</b><small>Gallery, Music, Recorder, PDF, Device Info, Weather, Dialer, Contacts, SMS, Calendar, Camera, Expenses, Tasks, RSS, Vault</small></div>
          <div class="layer mid"><b>Phase 4 &middot; 4</b><small>Keyboard, Launcher, Browser, App Manager</small></div>
        </div>
      </div>"""

    body = f"""{header("", "architecture.html")}
<main id="main">

  <section class="section">
    <div class="container">
      <p class="eyebrow">Architecture</p>
      <h1 class="page-title">Four modules, 24 apps, one rule.</h1>
      <p class="lead">Local-first, zero-tracking, no Google Play Services. This page is how the suite is actually put together, including where the build stands today.</p>
      <div class="actions">
        <a class="button primary" href="apps.html">The apps</a>
        <a class="button" href="#roadmap">Real status</a>
      </div>
    </div>
  </section>

  <section class="section section-band" id="layers">
    <div class="container">
      <div class="section-heading">
        <div><p class="eyebrow">1 &middot; Layers</p><h2 class="section-title">The foundation sits on nothing</h2></div>
        <div><p class="lead">Everything in the suite sits on these four repositories, and the apps sit on top of them.</p></div>
      </div>
{layers}
      <p class="note" style="margin-top:22px">F1, F2 and F3 are not decoration. If <code>nijatva-core</code> lands late, twenty apps grow twenty copies of the same Storage Access Framework helper. If <code>no-gms-check</code> lands late, the no-GMS claim stops being a build failure and becomes a promise.</p>
    </div>
  </section>

  <section class="section" id="screen">
    <div class="container">
      <div class="section-heading">
        <div><p class="eyebrow">2 &middot; One skeleton</p><h2 class="section-title">Learn one app, know all 24</h2></div>
        <div><p class="lead">Every app uses the same Compose skeleton, so a user who learns one app knows all twenty-four.</p></div>
      </div>
      <div class="phone">
        <div class="p-top"><span>&larr; Nijatva Notes</span><span class="off">Offline mode</span></div>
        <div class="p-banner"><span>SAF folder access: granted</span><span>INTERNET: not requested</span></div>
        <div class="p-body">the primary surface<br>Markdown editor, media grid, dialpad, reader</div>
        <div class="p-nav"><div class="on">Home</div><div>Vault / Local</div><div>Settings</div></div>
      </div>
      <h3 style="margin:34px 0 10px">Two rules are visible in the skeleton itself</h3>
      <p class="lead">The privacy state is on the screen, not buried in settings. A banner states whether storage access is granted and whether the app holds INTERNET. For the keyboard and the calculator the honest answer is "not requested", and saying it out loud is the product.</p>
      <p class="lead">The middle bar reads <strong>Vault / Local</strong>, never Cloud. There is no sync target to put there.</p>
    </div>
  </section>

  <section class="section section-band" id="roadmap">
    <div class="container">
      <div class="section-heading">
        <div><p class="eyebrow">3 &middot; Roadmap</p><h2 class="section-title">Roadmap and real status</h2></div>
        <div><p class="lead">28 repositories planned: 4 foundation repos and 24 apps. All four foundation repos exist, eight apps ship releases and one more has a repository. Status as of {UPDATED}.</p></div>
      </div>
      <div class="scroll">
      <table>
        <caption>Repository counts are planned totals, not a count of what exists today.</caption>
        <thead><tr><th scope="col">Phase</th><th scope="col">Scope</th><th scope="col">Repos</th><th scope="col">Apps</th><th scope="col">Target</th><th scope="col">Status</th></tr></thead>
        <tbody>
        <tr>
          <td class="ph">Phase 0</td><td>Foundation base</td><td class="num">4</td>
          <td class="apps">nijatva-core, no-gms-check, nijatva-design, nijatva-suite</td><td class="num">2-3 weeks</td>
          <td><span class="st st-done">4 repos, core has code</span></td>
        </tr>
        <tr>
          <td class="ph">Phase 1</td><td>Small apps</td><td class="num">5</td>
          <td class="apps">Calc, Clock, Notes, QR Scanner, Files</td><td class="num">4-6 weeks</td>
          <td><span class="st st-active">Files and Notes repos created</span></td>
        </tr>
        <tr>
          <td class="ph">Phase 2</td><td>Media and utility</td><td class="num">6</td>
          <td class="apps">Gallery, Music, Recorder, PDF Viewer, Device Info, Weather</td><td class="num">6-8 weeks</td>
          <td><span class="st st-done">Gallery and Music released</span></td>
        </tr>
        <tr>
          <td class="ph">Phase 3</td><td>Phone roles</td><td class="num">9</td>
          <td class="apps">Dialer, Contacts, SMS, Calendar, Camera, Expenses, Tasks, RSS, Vault</td><td class="num">8-10 weeks</td>
          <td><span class="st st-done">4 of 9 released</span></td>
        </tr>
        <tr>
          <td class="ph">Phase 4</td><td>Flagship</td><td class="num">4</td>
          <td class="apps">Keyboard, Launcher, Browser, App Manager</td><td class="num">10-12 weeks</td>
          <td><span class="st st-done">Browser released</span></td>
        </tr>
        </tbody>
      </table>
      </div>
      <p class="note" style="margin-top:22px">7 apps are easy, 12 medium and 5 hard. The timeline assumes part-time work and is a floor, not a promise. Seven apps have public releases (Browser, Camera, Gallery, Music, Dialer, Contacts, Messages); Files and Notes have repositories without one. Several of those releases are debug builds, which the app pages say plainly.</p>
      <h3 style="margin:34px 0 10px">Outside the 24</h3>
      <p class="lead">Seven projects sit beside the plan and are not counted in the table. Each has its own page on the apps screen: the Appstore, Photos, Video Player, Drive, Browser Mini X, Photo Editor and the Web Store. Two of them are not one app but a family: the video player ships for Android, Windows, macOS, Linux and the web from one Compose Multiplatform codebase, and <code>nijatva-video-player</code> is its Android-only sibling.</p>
    </div>
  </section>

  <section class="section" id="rules">
    <div class="container">
      <div class="section-heading">
        <div><p class="eyebrow">4 &middot; No-GMS</p><h2 class="section-title">BharOS and no-GMS compliance</h2></div>
        <div><p class="lead">What is banned, what replaces it, and why.</p></div>
      </div>
      <div class="scroll">
      <table>
        <thead><tr><th scope="col">Component</th><th scope="col">Never</th><th scope="col">Nijatva replacement</th><th scope="col">Note</th></tr></thead>
        <tbody>
        <tr><td class="ph">Push notifications</td><td class="no">Firebase Cloud Messaging</td><td class="yes">UnifiedPush / ntfy / foreground WebSocket</td><td class="apps">Most apps here need no push at all</td></tr>
        <tr><td class="ph">Storage access</td><td class="no">MANAGE_EXTERNAL_STORAGE</td><td class="yes">Storage Access Framework, Photo Picker</td><td class="apps">A revoked grant shows an empty state, not a crash</td></tr>
        <tr><td class="ph">Maps and location</td><td class="no">Google Maps SDK, FusedLocationProvider</td><td class="yes">osmdroid / MapLibre + OSM, LocationManager</td><td class="apps">Manual city entry is the primary path</td></tr>
        <tr><td class="ph">On-device ML</td><td class="no">ML Kit (Play Services variant)</td><td class="yes">Bundled TFLite / whisper.cpp / Vosk</td><td class="apps">Model ships in the APK, runs locally</td></tr>
        <tr><td class="ph">Ads</td><td class="no">AdMob</td><td class="yes">Nothing</td><td class="apps">An ad SDK is a tracking SDK</td></tr>
        <tr><td class="ph">Crash and analytics</td><td class="no">Crashlytics, Firebase Analytics</td><td class="yes">Nothing, or self-hosted Sentry; local log export</td><td class="apps">Default is nothing</td></tr>
        <tr><td class="ph">Accounts</td><td class="no">Google Sign-In</td><td class="yes">No account at all</td><td class="apps">This is the entire pitch</td></tr>
        <tr><td class="ph">App updates</td><td class="no">Play Core in-app updates</td><td class="yes">Own F-Droid style index on Pages</td><td class="apps">nijatva-suite does this</td></tr>
        <tr><td class="ph">Distribution</td><td class="no">Play Store</td><td class="yes">APK repository, Nijatva Appstore, F-Droid, sideload</td><td class="apps">Signing key never in the repo</td></tr>
        </tbody>
      </table>
      </div>
    </div>
  </section>

  <section class="section section-band" id="corrections" style="border-bottom:0">
    <div class="container">
      <div class="section-heading">
        <div><p class="eyebrow">5 &middot; Corrections</p><h2 class="section-title">Two mistakes, recorded</h2></div>
        <div><p class="lead">Kept on the page so the same two do not come back.</p></div>
      </div>
      <div class="fix">
        <b>nijatva-core does not sync anything</b>
        <p>The first draft described core as "Compose UI + SAF + Sync". There is no sync in a local-first suite. Core carries the design system, SAF helpers, a text-to-speech wrapper, encrypted preferences and local backup and restore.</p>
      </div>
      <div class="fix">
        <b>AdMob is advertising, not analytics</b>
        <p>The draft grouped "AdMob / Crashlytics" under one heading. They are two separate bans: no ad SDK, and no analytics SDK. The second is the one people forget, because a crash reporter usually ships telemetry along with it.</p>
      </div>
      <div class="cards" style="margin-top:30px">
        <div class="card"><h3>Repository naming</h3><p><code>nijatva-&lt;app&gt;</code>, lowercase and hyphenated. Foundation repos follow the same rule.</p></div>
        <div class="card"><h3>Package name</h3><p><code>in.nijatva.&lt;app&gt;</code>, fallback <code>com.nijatva.&lt;app&gt;</code>. Locked before the first release.</p></div>
        <div class="card"><h3>Display name</h3><p><code>Nijatva &lt;App&gt;</code>, one prefix everywhere, never abbreviated.</p></div>
      </div>
    </div>
  </section>

</main>
{footer("")}"""
    return head("Architecture — Nijatva",
                "How the Nijatva suite is structured: four foundation modules, 24 Android apps, one screen skeleton, and the rules that keep Google Play Services out.",
                SITE + "/architecture.html") + body



# ---------------------------------------------------------------- developer
def build_developer():
    # facts pulled from the GitHub API on 13 November 2026; update the numbers here
    repos = 28
    apps = len(SUITE)
    shipped = len([a for a in APPS if a["status"] == "shipped"])
    coded = len([a for a in APPS if a["status"] != "planned"])
    maintain = [a for a in APPS if a["status"] != "planned"]
    # drop a square photo at assets/developer.jpg and rebuild to replace the monogram
    photo = ROOT / "assets" / "developer.jpg"
    avatar = ('<img src="assets/developer.jpg" alt="Vasudev Dangaya">' if photo.exists()
              else '<span aria-hidden="true">VD</span>')
    icons = "\n".join(
        f'        <a href="apps/{a["slug"]}.html" title="{E(a["name"])}">'
        f'<img src="assets/icons/{a["slug"]}.svg" alt="{E(a["name"])}" width="46" height="46"></a>'
        for a in maintain)

    body = f"""{header("", "developer.html")}
<main id="main">

  <div class="container dev-top">
    <a class="dev-back" href="index.html">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M19 12H5"/><path d="M12 19l-7-7 7-7"/></svg>
      Developer
    </a>
  </div>

  <section class="dev-hero">
    <div class="container">
      <div class="avatar">{avatar}</div>
      <h1>Vasudev Dangaya</h1>
      <p class="dev-handle">@vasudev-work</p>
      <p class="dev-bio">Builds Android apps in Kotlin and Jetpack Compose, without Google Play Services.</p>
      <p class="dev-bio">Nijatva is the current project: {apps} small apps, no accounts, no ads, no analytics.</p>

      <div class="dev-stats" role="list">
        <div role="listitem"><b>{repos}</b><span>Repositories</span></div>
        <div role="listitem"><b>{apps}</b><span>Apps planned</span></div>
        <div role="listitem"><b>{coded}</b><span>With code today</span></div>
      </div>

      <div class="dev-rows">
        <div class="dev-row">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21s7-6.3 7-11a7 7 0 1 0-14 0c0 4.7 7 11 7 11z"/><circle cx="12" cy="10" r="2.6"/></svg>
          <span>India</span>
        </div>
        <div class="dev-row">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1.5 1.5"/><path d="M14 11a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7L12.5 19.5"/></svg>
          <a href="{SITE}/">{SITE.replace("https://", "")}</a>
        </div>
        <div class="dev-row">
          <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2.5"/><path d="M3.5 7l8.5 6 8.5-6"/></svg>
          <a href="mailto:{EMAIL}">{EMAIL}</a>
        </div>
      </div>

      <a class="btn-github" href="{GH_USER}">
        <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82a7.4 7.4 0 0 1 2-.27c.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8z"/></svg>
        View GitHub Profile
      </a>

      <div class="maintains">
        <h2>Maintains</h2>
        <div class="maintain-icons">
{icons}
        <span class="maintain-more">+{apps - len(maintain)}</span>
        </div>
        <p class="maintain-note">{len(maintain)} of the {apps} apps have a repository today; the other {apps - len(maintain)} are planned and listed on the <a href="apps.html">apps page</a>. Figures read from GitHub on {UPDATED}.</p>
      </div>
    </div>
  </section>

</main>
{footer("")}"""
    return head("Developer — Nijatva",
                "Vasudev Dangaya, independent developer in India. Builds Nijatva: 24 small Android apps without Google Play Services, accounts, ads or analytics.",
                SITE + "/developer.html") + body



# ---------------------------------------------------------------- search
SEARCH_SCRIPT = """
(function () {
  var INDEX = window.NIJATVA_INDEX || [];
  var q = document.getElementById("q");
  var list = document.getElementById("results");
  var count = document.getElementById("count");
  var all = INDEX.slice();

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  function mark(text, needle) {
    if (!needle) return esc(text);
    var i = text.toLowerCase().indexOf(needle);
    if (i < 0) return esc(text);
    return esc(text.slice(0, i)) + "<mark>" + esc(text.slice(i, i + needle.length)) + "</mark>" + esc(text.slice(i + needle.length));
  }

  function score(item, terms) {
    var name = item.n.toLowerCase();
    var keys = (item.k || "").toLowerCase();
    var sum = (item.s || "").toLowerCase();
    var total = 0;
    for (var t = 0; t < terms.length; t++) {
      var term = terms[t];
      if (name === term) total += 100;
      else if (name.indexOf(term) === 0) total += 60;
      else if (name.indexOf(term) > -1) total += 40;
      else if (keys.indexOf(term) > -1) total += 18;
      else if (sum.indexOf(term) > -1) total += 8;
      else return 0;                       // every term has to match somewhere
    }
    return total;
  }

  function render(items, terms, query) {
    list.innerHTML = "";
    if (!items.length) {
      list.innerHTML = '<li class="search-empty">Nothing matches <strong>' + esc(query) +
        '</strong>. Try "notes", "browser", "vault" or "camera".</li>';
      count.textContent = "";
      return;
    }
    count.textContent = items.length + (items.length === 1 ? " result" : " results");
    items.forEach(function (item) {
      var li = document.createElement("li");
      li.className = "search-hit";
      li.innerHTML =
        '<a href="' + item.u + '">' +
          '<img src="assets/icons/' + item.i + '.svg" alt="" width="44" height="44" loading="lazy">' +
          "<div>" +
            "<strong>" + mark(item.n, terms[0]) + "</strong>" +
            '<span class="search-kind">' + esc(item.st) + "</span>" +
            "<p>" + esc(item.s) + "</p>" +
          "</div>" +
        "</a>";
      list.appendChild(li);
    });
  }

  function run() {
    var query = q.value.trim().toLowerCase();
    if (!query) {
      render(all.slice(0, 8), [], "");
      count.textContent = INDEX.length + " apps and pages. Start typing.";
      return;
    }
    var terms = query.split(/\\s+/).filter(Boolean);
    var hits = all
      .map(function (item) { return { item: item, s: score(item, terms) }; })
      .filter(function (r) { return r.s > 0; })
      .sort(function (a, b) { return b.s - a.s || a.item.n.localeCompare(b.item.n); })
      .map(function (r) { return r.item; });
    render(hits, terms, q.value.trim());
  }

  q.addEventListener("input", run);
  document.addEventListener("keydown", function (e) {
    if (e.key === "/" && document.activeElement !== q) { e.preventDefault(); q.focus(); }
    if (e.key === "Escape" && document.activeElement === q) { q.value = ""; run(); q.blur(); }
  });

  var params = new URLSearchParams(location.search);
  if (params.get("q")) { q.value = params.get("q"); }
  run();
})();
"""


def build_search():
    entries = []
    for a in APPS:
        kind = "App" if a.get("suite", True) else "Ecosystem"
        words = " ".join([a["name"], a["slug"], a["summary"]] + a["features"]).lower()
        entries.append({"n": a["name"], "u": "apps/%s.html" % a["slug"], "i": a["slug"],
                        "s": a["summary"], "k": words, "st": kind + " \u00b7 " + STATUS_LABEL[a["status"]]})
    entries.append({"n": "All apps", "u": "apps.html", "i": "launcher", "st": "Page",
                    "s": "The full list, grouped by phase, with the real release status of each app.",
                    "k": "apps list suite directory all twenty four"})
    entries.append({"n": "Architecture", "u": "architecture.html", "i": "core", "st": "Page",
                    "s": "Layers, the shared screen skeleton, the roadmap table and the no-GMS rules.",
                    "k": "architecture layers roadmap status no-gms firebase bharos degoogled"})
    entries.append({"n": "Developer", "u": "developer.html", "i": "appmanager", "st": "Page",
                    "s": "Who builds Nijatva, what the numbers are, and where the source lives.",
                    "k": "developer vasudev dangaya profile contact github"})
    entries.append({"n": "Why Nijatva", "u": "index.html#why", "i": "notes", "st": "Page",
                    "s": "What the name means and what the project is trying to do.",
                    "k": "why name sanskrit meaning about nijatva"})

    index_js = "window.NIJATVA_INDEX = " + json.dumps(entries, ensure_ascii=False) + ";"

    body = f"""{header("", "search.html")}
<main id="main">
  <section class="section" style="border-bottom:0">
    <div class="container search-wrap">
      <p class="eyebrow">Search</p>
      <h1 class="page-title">Find an app</h1>
      <p class="lead" style="max-width:56ch">Type a name, a job or a word from the description. Press <kbd>/</kbd> anywhere on the site to come back here.</p>

      <div class="search-box">
        <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="6.4"/><path d="M15.6 15.6L21 21"/></svg>
        <input id="q" type="search" placeholder="notes, browser, vault, camera..." autocomplete="off" autofocus aria-label="Search apps and pages">
      </div>

      <p class="search-count" id="count"></p>
      <ul class="search-results" id="results"></ul>
    </div>
  </section>
</main>
<script>{index_js}</script>
<script>{SEARCH_SCRIPT}</script>
{footer("")}"""
    return head("Search — Nijatva", "Search every Nijatva app and page by name, job or feature.",
                SITE + "/search.html") + body


# ---------------------------------------------------------------- 404 + static
def build_404():
    body = f"""{header("", "")}
<main id="main">
  <div class="container notfound">
    <div>
      <h1>404</h1>
      <p class="lead" style="margin:14px auto 0">This page is not part of the suite.</p>
      <div class="actions" style="justify-content:center">
        <a class="button primary" href="/">Back to Nijatva</a>
        <a class="button" href="/apps.html">All apps</a>
      </div>
    </div>
  </div>
</main>
{footer("")}"""
    return head("Not found — Nijatva", "This page is not part of the Nijatva suite.",
                SITE + "/404.html", image=False,
                extra='<meta name="robots" content="noindex">\n') + body


def build_camera_page():
    """The camera's project page.

    Modelled on the pages the other apps have: a hero that says what the thing is and
    what it costs you, two ways in, then the work itself. Every number on it was read
    from the app - the permissions from its manifest, the API level from its build
    file, the size from a built APK - rather than guessed.
    """
    app = next(a for a in APPS if a["slug"] == "camera")
    # The page is served from /camera/about/, two levels below the site root.
    root = "../../"

    def card(icon, title, text):
        return f"""        <article class="card">
          <div style="display:flex;align-items:center;gap:12px">
            <span style="display:grid;place-items:center;width:38px;height:38px;border-radius:11px;
                         background:var(--accent-soft);color:var(--accent);flex:none">{icon}</span>
            <h3 style="margin:0;font-size:16px">{E(title)}</h3>
          </div>
          <p style="margin:0;color:var(--ink-soft);font-size:14.5px;line-height:1.55">{E(text)}</p>
        </article>"""

    def stat(text):
        return f'<span class="badge">{E(text)}</span>'

    I_AIM = '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7"><circle cx="12" cy="12" r="7.2"/><path d="M12 4.8v3M12 16.2v3M4.8 12h3M16.2 12h3"/></svg>'
    I_RAW = '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7"><rect x="4" y="5" width="16" height="14" rx="2.5"/><path d="M4 10h16M9 10v9"/></svg>'
    I_NIGHT = '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M20 14.5A8 8 0 1 1 9.5 4a6.4 6.4 0 0 0 10.5 10.5z"/></svg>'
    I_HDR = '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7"><circle cx="12" cy="12" r="4"/><path d="M12 2.8v3M12 18.2v3M2.8 12h3M18.2 12h3M5.4 5.4l2.1 2.1M16.5 16.5l2.1 2.1M18.6 5.4l-2.1 2.1M7.5 16.5l-2.1 2.1"/></svg>'
    I_GRADE = '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M4 16.5l4.5-9 4 7 3-4.5 4 6.5z"/><path d="M4 20h16"/></svg>'
    I_FRAME = '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M4 8V5.5A1.5 1.5 0 0 1 5.5 4H8M16 4h2.5A1.5 1.5 0 0 1 20 5.5V8M20 16v2.5a1.5 1.5 0 0 1-1.5 1.5H16M8 20H5.5A1.5 1.5 0 0 1 4 18.5V16"/><path d="M12 8.5v7M8.5 12h7"/></svg>'
    I_SUITE = '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7"><rect x="4" y="4" width="7" height="7" rx="1.6"/><rect x="13" y="4" width="7" height="7" rx="1.6"/><rect x="4" y="13" width="7" height="7" rx="1.6"/><rect x="13" y="13" width="7" height="7" rx="1.6"/></svg>'

    cards = "\n".join([
        card(I_AIM, "Pro controls",
             "Manual ISO, shutter time and focus behind CONTROL_AE_MODE_OFF, with a live "
             "readout of what the sensor is actually doing."),
        card(I_RAW, "RAW and DNG",
             "RAW capture written as a DNG, and a 10-bit packed path where the sensor allows "
             "it - half the file, same information."),
        card(I_NIGHT, "Night and astro stacking",
             "Pyramid alignment and an inverse-variance merge in our own C++, then demosaic, "
             "white balance and a tone curve that puts 18% grey where it belongs."),
        card(I_HDR, "Auto HDR",
             "When the frame is clipping, a plain photo quietly becomes a short burst and is "
             "merged, so the sky keeps its colour instead of turning white."),
        card(I_GRADE, "Grading after the shot",
             "Five looks, per-lens tuning, four sliders and an optional portrait blur. The "
             "same pipeline every time, so a look can never break a capture."),
        card(I_FRAME, "Framing aids",
             "Grid, horizon level with a haptic tick, focus peaking and a histogram - and the "
             "photo keeps the exposure and white balance the preview showed you."),
        card(I_SUITE, "Part of a suite",
             "Hands shots to Nijatva Gallery and Nijatva Photos, and accepts IMAGE_CAPTURE and "
             "VIDEO_CAPTURE, so any other app can ask it for a photo."),
    ])

    body = f"""{header(root, "apps.html")}
<main id="main">

  <section class="section">
    <div class="container">
      <div class="app-hero-head">
        <img class="app-icon" src="{root}assets/icons/camera.svg" alt="" width="52" height="52">
        <div>
          <p class="eyebrow">Project page</p>
          <h1 class="hero-title">{E(app["name"])}</h1>
        </div>
      </div>
      <p class="lead">Camera2 with manual controls, RAW, night stacking, exposure fusion and
      panorama - and the maths written here, not borrowed.</p>
      <div class="badge-row" style="margin:0 0 22px">
        {stat("Android 10+")}{stat("11 MB APK")}{stat("No INTERNET permission")}
        {stat("0 trackers")}{stat("English + हिंदी")}
      </div>
      <div class="actions">
        <a class="button primary" href="{GH}/nijatva-camera/releases/latest">{ICON_DOWNLOAD}Download the APK</a>
        <a class="button primary" href="{root}camera/">{ICON_PLAY}Open the web app</a>
        <a class="button" href="{GH}/nijatva-camera">{ICON_LINK}View source</a>
      </div>
    </div>
  </section>

  <section class="section section-band">
    <div class="container">
      <div class="section-heading">
        <div><p class="eyebrow">Two ways to use it</p><h2 class="section-title">Same idea, two engines</h2></div>
        <div><p class="lead">Pick whichever fits the moment.</p></div>
      </div>
      <div class="grid two">
        <article class="card">
          <h3 style="margin:0 0 4px">Android app</h3>
          <p style="margin:0;color:var(--ink-soft)">The whole camera: manual ISO, shutter and
          focus, RAW and DNG, night and astro stacking, Auto HDR, panorama, looks and sliders.
          Works with no network at all.</p>
          <div class="app-card-actions">
            <a class="button primary" href="{GH}/nijatva-camera/releases/latest">{ICON_DOWNLOAD}Download</a>
          </div>
        </article>
        <article class="card">
          <h3 style="margin:0 0 4px">Web app</h3>
          <p style="margin:0;color:var(--ink-soft)">Runs in a browser tab: live viewfinder,
          grid, front and back, capture straight to your device. No install, no account.
          What a browser cannot give it - manual exposure, RAW, stacking - it does not
          pretend to.</p>
          <div class="app-card-actions">
            <a class="button" href="{root}camera/">{ICON_PLAY}Open the web app</a>
          </div>
        </article>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="container">
      <div class="section-heading">
        <div><p class="eyebrow">What it does</p><h2 class="section-title">Everything a photo needs</h2></div>
        <div><p class="lead">Nothing on this list needs an account, a server or a Play Services library.</p></div>
      </div>
      <div class="grid three">
{cards}
      </div>
    </div>
  </section>

  <section class="section section-band">
    <div class="container">
      <div class="section-heading">
        <div><p class="eyebrow">How it is built</p><h2 class="section-title">Camera2, and our own maths</h2></div>
      </div>
      <ul class="feature-list">
        <li>Camera2 API directly. No CameraX, no Play Services, no analytics, no ads</li>
        <li>Two permissions in total: <code>CAMERA</code> and <code>RECORD_AUDIO</code>. No
            <code>INTERNET</code>, so nothing can leave the phone even by accident</li>
        <li>Night, astro and HDR merge run in C++: pyramid alignment, inverse-variance merge,
            demosaic, white balance, colour matrix, tone curve</li>
        <li>Grading is Kotlin, after the capture: looks, per-lens tuning, four sliders,
            chroma denoise, thresholded sharpening, optional portrait blur</li>
        <li>The preview and the photo agree: the capture locks the preview's exposure and
            white balance, and the framing maths match what the viewfinder showed</li>
      </ul>
      <p class="lead" style="margin-top:22px">Build it from a plain checkout - JDK 17, SDK 35,
      NDK 27.2.12479018 and CMake 3.22.1, all pinned by the native module.</p>
      <pre style="margin:0 0 16px;padding:14px 16px;border-radius:10px;overflow-x:auto;
                  background:var(--surface-quiet);border:1px solid var(--line);
                  font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
                  font-size:13px;line-height:1.6;color:var(--ink-soft)">git clone https://github.com/nijatva/nijatva-camera
cd nijatva-camera
./gradlew :app:assembleFullDebug</pre>
      <p class="note">{E(app.get("note", ""))}</p>
      <div class="actions">
        <a class="button" href="{root}apps/camera.html">The app page</a>
        <a class="button" href="{GH}/nijatva-camera/blob/main/docs/INTEROP.md">How it talks to the suite</a>
      </div>
    </div>
  </section>

</main>
{footer(root)}"""
    out = ROOT / "camera" / "about"
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(
        head("Camera — Nijatva", app["summary"], SITE + "/camera/about/", root=root)
        + body)
    return "camera/about/index.html"


def build_static():
    urls = [("", "1.0", "weekly"), ("apps.html", "0.9", "weekly"),
            ("architecture.html", "0.8", "monthly"), ("developer.html", "0.5", "monthly"),
            ("search.html", "0.4", "monthly")]
    urls += [(f"apps/{a['slug']}.html", "0.6", "monthly") for a in APPS]
    # A browser build served from this repository is a page of this site, so it belongs
    # in the sitemap. Absolute URLs point at another repository's Pages site, which has
    # its own sitemap; listing them here would claim pages this site does not serve.
    urls += [(a["web"], "0.7", "monthly") for a in APPS + ECOSYSTEM
             if a.get("web") and not a["web"].startswith("http")]
    urls += [("camera/about/", "0.7", "monthly")]
    entries = "\n".join(
        f"  <url>\n    <loc>{SITE}/{u}</loc>\n    <lastmod>2026-11-13</lastmod>\n"
        f"    <changefreq>{c}</changefreq>\n    <priority>{p}</priority>\n  </url>" for u, p, c in urls)
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + entries + "\n</urlset>\n")
    (ROOT / "robots.txt").write_text(
        "User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % SITE)

    # favicon: the N mark from the old site, as a file
    (ROOT / "assets" / "favicon.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64" role="img" aria-label="Nijatva">\n'
        '  <rect width="64" height="64" rx="14" fill="#1b1f45"/>\n'
        '  <path d="M20 46V18l24 28V18" fill="none" stroke="#e8a33d" stroke-width="6" '
        'stroke-linecap="round" stroke-linejoin="round"/>\n</svg>\n')
    return len(urls)


if __name__ == "__main__":
    (ROOT / "index.html").write_text(build_index())
    (ROOT / "apps.html").write_text(build_apps())
    (ROOT / "architecture.html").write_text(build_architecture())
    (ROOT / "404.html").write_text(build_404())
    (ROOT / "developer.html").write_text(build_developer())
    (ROOT / "search.html").write_text(build_search())
    slugs = build_app_pages()
    camera_page = build_camera_page()
    n_urls = build_static()
    print("index, apps, architecture, developer, search, 404 written")
    print("%d app pages written" % len(slugs))
    print("%s written" % camera_page)
    print("%d sitemap urls" % n_urls)
