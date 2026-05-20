# Ameblo Ingestion Workflow

This document describes the theme-limited Ameblo ingestion workflow for Playbook Text research.

## Purpose

The workflow collects a small number of article URLs and metadata from approved Kinegawa Reds Ameblo themes. It supports future Playbook Text theme extraction without turning the repository into an Ameblo article archive.

## Allowed Sources

Only the five theme URLs in `data/ameblo/theme_sources.json` are allowed:

- ちょっと真面目な野球話
- 木根川レッズ野球編
- 木根川レッズ全般
- 木根川レッズ基礎編
- 学童野球全般

The workflow does not crawl global archives, unrelated themes, external links, or the whole Ameblo site.

## Schedule

GitHub Actions runs the workflow every 6 hours:

```yaml
schedule:
  - cron: "0 */6 * * *"
```

Manual execution is also available through `workflow_dispatch`. The default limit is 10 article URLs per run.

## Data Policy

Ameblo article URLs are preserved, but full article bodies are not stored in the Git repository.

Repository data is limited to:

- URL
- entry ID
- theme ID and label
- title
- published date if available
- fetched timestamp
- fetch status
- text length
- short review excerpt
- detected keywords
- candidate phrases
- internal summary
- classification metadata

`data/ameblo/raw_articles/` is treated as a local or Actions working cache. Raw HTML and text files in that directory are ignored by Git.

## Scripts

Run discovery only:

```bash
python3 scripts/discover_ameblo_theme_articles.py --dry-run
python3 scripts/discover_ameblo_theme_articles.py
```

Run a small ingestion batch:

```bash
python3 scripts/ingest_ameblo_batch.py --limit 10 --dry-run
python3 scripts/ingest_ameblo_batch.py --limit 10
```

Extract Playbook Text candidates:

```bash
python3 scripts/extract_playbook_theme_candidates.py
```

## Outputs

- `data/ameblo/ingestion_state.json`
- `data/ameblo/parsed_articles/*.json`
- `data/ameblo/ingestion_logs/*.json`
- `data/playbook-text/discovery/theme-candidates.json`
- `docs/playbook-text/discovery-summary.md`

## Guardrails

- Do not bypass robots.txt.
- Do not use login, cookies, CAPTCHA bypass, or access control bypass.
- Do not increase request frequency casually.
- Do not add public HTML references until owner review.
- Do not publish long Ameblo text.
- Do not include children’s personal information.
- Do not change GitHub Pages settings from this workflow.
