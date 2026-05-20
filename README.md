# reds-playbook

Coaching playbook for Kinegawa Reds youth baseball, built as a mobile-first static website for GitHub Pages.

## Site pages

- `index.html` - top page and section hub
- `regular-practice-menu.html` - standard practice menu
- `policy-mindset.html` - coaching policy and team mindset
- `Horizontal-balance.html` - horizontal balance teaching page
- `3runner-forward-grounder.html` - interactive front-defense case playbook

## Local review

From the repository root:

```bash
python3 -m http.server 8000
```

Then open:

```text
http://127.0.0.1:8000/
```

The site is deployable directly from the repository root with GitHub Pages.

## Access gate

This site uses a lightweight client-side access gate for casual viewing control.
To rotate the access code, open `tools/hash-passcode.html`, generate a SHA-256 hash, and replace `ALLOWED_PASSCODE_HASH` in `auth.js` with that hash.

Do not commit the raw access code.

## Ameblo content mapping pipeline

The Ameblo pipeline is a local content-planning tool. It is not linked from public site navigation and does not change GitHub Pages deployment.

Run from the repository root:

```bash
python3 scripts/discover_ameblo_urls.py
python3 scripts/fetch_ameblo.py --max-articles 50
python3 scripts/build_ameblo_index.py
python3 scripts/map_ameblo_to_playbook.py
```

For a smaller test:

```bash
python3 scripts/discover_ameblo_urls.py
python3 scripts/fetch_ameblo.py --max-articles 20
```

Outputs are saved under:

- `data/ameblo/articles.json`
- `data/ameblo/articles.csv`
- `data/ameblo/discovered_urls.json`
- `data/ameblo/source_urls.txt`
- `data/ameblo/article_index.json`
- `data/ameblo/raw/`
- `docs/content-source-map.md`
- `docs/keyword-taxonomy.md`

Source Ameblo article URLs are preserved in:

- `data/ameblo/articles.json`
- `data/ameblo/article_index.json`
- `docs/content-source-map.md`

Notes:

- The scripts use Python standard library only.
- Respect public access limits and robots.txt. If fetching is blocked, do not bypass it.
- Do not paste raw passcodes into source files.
- Do not copy long blog text verbatim into public pages.
- Do not include personal information about children.
- Public `参考記事` links should be added only after owner review.
