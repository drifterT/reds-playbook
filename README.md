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
python3 scripts/fetch_ameblo.py --input data/ameblo/discovered_urls.json --max-articles 50
python3 scripts/build_ameblo_index.py
python3 scripts/map_ameblo_to_playbook.py
```

For a smaller test:

```bash
python3 scripts/discover_ameblo_urls.py
python3 scripts/fetch_ameblo.py --input data/ameblo/discovered_urls.json --max-articles 20
```

Outputs are saved under:

- `data/ameblo/articles.json`
- `data/ameblo/articles.csv`
- `data/ameblo/discovered_urls.json`
- `data/ameblo/source_urls.txt`
- `data/ameblo/article_index.json`
- `data/ameblo/manual_articles/`
- `data/ameblo/raw/`
- `docs/content-source-map.md`
- `docs/keyword-taxonomy.md`

Source Ameblo article URLs are preserved in:

- `data/ameblo/articles.json`
- `data/ameblo/article_index.json`
- `docs/content-source-map.md`

### Manual Ameblo article input

When robots.txt blocks automatic article fetching, keep the URL and add only the articles that need review by hand.

1. Add article URLs, one per line, to `data/ameblo/source_urls.txt`.
2. Run discovery and fetch to record URL status:

```bash
python3 scripts/discover_ameblo_urls.py
python3 scripts/fetch_ameblo.py --input data/ameblo/discovered_urls.json --max-articles 20
```

3. Check blocked or failed URLs in `data/ameblo/failed_urls.json`.
4. For a selected article, create a file under `data/ameblo/manual_articles/`, for example `data/ameblo/manual_articles/entry-12555442306.md`:

```markdown
---
url: https://ameblo.jp/kinegawareds/entry-12555442306.html
title: Optional title
date: Optional date
source_type: manual_copy
---

Paste a short manually supplied text excerpt or working summary here.
```

5. Regenerate the index and planning map:

```bash
python3 scripts/build_ameblo_index.py
python3 scripts/map_ameblo_to_playbook.py
```

Manual article bodies are indexed as `manual_body_added` and classified with the same taxonomy rules as fetched articles. Keep the original Ameblo URL in the metadata so future `参考記事` links can point to the public source URL.

Notes:

- The scripts use Python standard library only.
- Respect public access limits and robots.txt. If fetching is blocked, do not bypass it.
- Do not paste raw passcodes into source files.
- Do not copy long blog text verbatim into public pages.
- Do not include personal information about children.
- Public `参考記事` links should be added only after owner review.
