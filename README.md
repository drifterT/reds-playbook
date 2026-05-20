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
Before publishing with a real access code, open `tools/hash-passcode.html`, generate a SHA-256 hash, and replace `PASSCODE_HASH_PLACEHOLDER` in `auth.js` with that hash.

Do not commit the raw access code.
