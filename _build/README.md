# How this site is built

The HTML is generated. Nothing in `apps/`, `apps.html`, `index.html`, `sitemap.xml` or
`robots.txt` should be edited by hand — edit the data or the template, then regenerate:

```
python3 _build/build.py
```

| File | What it is |
|---|---|
| `_build/apps_data.py` | One `dict` per app: slug, name, phase, size, status, tile, summary, features, note, and `web` when the app has a browser build |
| `_build/build.py` | The templates: `app_card()`, `build_index()`, `build_app_pages()`, `build_architecture()`, `build_developer()`, sitemap, robots |
| `_build/tokens.py`, `_build/gen_icons.py` | Design tokens and the icon generator |

## Browser builds

An app with a browser version gets a folder at the repository root named after its slug
(`camera/`, `notes/`, `gallery/`) holding a self-contained `index.html`, and a `web`
field in its `dict`:

```python
dict(slug="gallery", ..., web="gallery/", note="v0.1.3 debug build, 17 November 2026."),
```

The path is relative to the site root — `gallery/`, never `/gallery/`.
`build_app_pages()` turns that field into the "Open in the browser" button on the app's
page, so the field is the whole feature: no template edit per app.

## Two rules, learned the hard way

1. **Pull before you regenerate.** `git pull --rebase` first. Rebuilding from an out-of-date
   `apps_data.py` silently reverts whatever landed on `main` since — status changes, `web`
   fields, features, notes. That is how the gallery's browser button disappeared once and
   how the Notes app went back to "in progress".
2. **Read `git diff` before you commit build output.** A correct rebuild touches only the
   pages whose data changed. If a rebuild rewrites pages you did not mean to touch, the
   data is stale: stop, pull, regenerate again. Commit the data change and its generated
   pages together, in one commit.

More than one process pushes to this branch. A build commit that carries unrelated page
changes is almost always a stale-data build, not an improvement.
