#!/usr/bin/env python3
"""Discover article URLs only from the approved Ameblo theme pages."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import time

from ameblo_ingest_common import (
    ARTICLE_RE,
    THEME_RE,
    can_fetch,
    fetch_url,
    load_robots,
    normalize_url,
    now_iso,
    read_json,
    write_json,
)


LINK_RE = re.compile(r"""href=["']([^"']+)["']""", re.I)


def default_state() -> dict:
    return {
        "last_run_at": None,
        "max_articles_per_run": 10,
        "processed_urls": {},
        "pending_urls": [],
        "failed_urls": [],
        "blocked_urls": [],
        "skipped_urls": [],
    }


def enabled_themes(theme_sources: dict) -> list[dict]:
    return [item for item in theme_sources.get("allowed_theme_sources", []) if item.get("enabled")]


def pending_urls_by_url(state: dict) -> dict[str, dict]:
    return {item["url"]: item for item in state.get("pending_urls", []) if item.get("url")}


def known_urls(state: dict) -> set[str]:
    urls = set(state.get("processed_urls", {}).keys())
    for key in ("pending_urls", "failed_urls", "blocked_urls", "skipped_urls"):
        for item in state.get(key, []):
            if item.get("url"):
                urls.add(item["url"])
    return urls


def extract_article_urls(html_text: str, base_url: str, theme: dict) -> list[dict]:
    found: dict[str, dict] = {}
    for raw_href in LINK_RE.findall(html_text):
        url = normalize_url(raw_href, base_url)
        if not ARTICLE_RE.fullmatch(url):
            continue
        found[url] = {
            "url": url,
            "theme_id": theme["id"],
            "theme_label": theme["label"],
        }
    return sorted(found.values(), key=lambda item: item["url"])


def extract_next_theme_pages(html_text: str, base_url: str, allowed_theme_url: str) -> list[str]:
    pages = set()
    theme_base = allowed_theme_url.replace(".html", "")
    for raw_href in LINK_RE.findall(html_text):
        url = normalize_url(raw_href, base_url)
        if THEME_RE.fullmatch(url) and url.startswith(theme_base):
            pages.add(url)
    return sorted(pages)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--theme-sources", default="data/ameblo/theme_sources.json")
    parser.add_argument("--state", default="data/ameblo/ingestion_state.json")
    parser.add_argument("--delay-seconds", type=float, default=2.0)
    parser.add_argument("--max-pages-per-theme", type=int, default=1)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    theme_sources = read_json(Path(args.theme_sources), {"allowed_theme_sources": []})
    state_path = Path(args.state)
    state = read_json(state_path, default_state())
    themes = enabled_themes(theme_sources)
    timestamp = now_iso()

    if args.dry_run:
        print(f"Dry run: {len(themes)} allowed theme sources")
        for theme in themes:
            print(f"- {theme['label']}: {theme['url']}")
        print("No network fetch or state update performed.")
        return 0

    robots = load_robots()
    existing = known_urls(state)
    pending = pending_urls_by_url(state)
    discovered_count = 0
    blocked_count = 0
    failed_count = 0

    for theme in themes:
        queue = [theme["url"]]
        seen_pages: set[str] = set()
        while queue and len(seen_pages) < args.max_pages_per_theme:
            page_url = queue.pop(0)
            if page_url in seen_pages:
                continue
            seen_pages.add(page_url)
            if not can_fetch(robots, page_url):
                state.setdefault("blocked_urls", []).append({
                    "url": page_url,
                    "theme_id": theme["id"],
                    "theme_label": theme["label"],
                    "status": "blocked",
                    "stage": "discover",
                    "first_seen_at": timestamp,
                    "last_attempt_at": timestamp,
                    "attempt_count": 1,
                    "error": "blocked_by_robots",
                })
                blocked_count += 1
                continue
            status, body, err = fetch_url(page_url)
            if err or status >= 400 or not body:
                state.setdefault("failed_urls", []).append({
                    "url": page_url,
                    "theme_id": theme["id"],
                    "theme_label": theme["label"],
                    "status": "failed",
                    "stage": "discover",
                    "first_seen_at": timestamp,
                    "last_attempt_at": timestamp,
                    "attempt_count": 1,
                    "error": err or f"HTTP status {status}",
                })
                failed_count += 1
                continue
            for article in extract_article_urls(body, page_url, theme):
                if article["url"] in existing:
                    continue
                pending[article["url"]] = {
                    **article,
                    "status": "pending",
                    "first_seen_at": timestamp,
                    "last_attempt_at": None,
                    "attempt_count": 0,
                    "raw_path": None,
                    "parsed_path": None,
                    "error": None,
                }
                existing.add(article["url"])
                discovered_count += 1
            for next_page in extract_next_theme_pages(body, page_url, theme["url"]):
                if next_page not in seen_pages and next_page not in queue:
                    queue.append(next_page)
            time.sleep(args.delay_seconds)

    state["pending_urls"] = sorted(pending.values(), key=lambda item: (item["theme_id"], item["url"]))
    write_json(state_path, state)
    print(f"Allowed themes: {len(themes)}")
    print(f"New pending article URLs: {discovered_count}")
    print(f"Blocked theme pages: {blocked_count}")
    print(f"Failed theme pages: {failed_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
