#!/usr/bin/env python3
"""Collect Ameblo article URL candidates from local/manual sources.

This layer is intentionally separate from fetching article bodies. It does not
scrape search engines and does not bypass robots.txt. It only extracts article
URLs from local files and previous pipeline outputs.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import time


ARTICLE_RE = re.compile(r"https://ameblo\.jp/kinegawareds/entry-\d+\.html")


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def read_json(path: Path, default):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def extract_urls(text: str) -> set[str]:
    return set(ARTICLE_RE.findall(text))


def add_url(records: dict[str, dict], url: str, source: str, discovered_at: str) -> None:
    if url not in records:
        records[url] = {
            "url": url,
            "sources": [],
            "source": source,
            "discovered_at": discovered_at,
            "status": "pending",
        }
    if source not in records[url]["sources"]:
        records[url]["sources"].append(source)
    records[url]["source"] = " | ".join(records[url]["sources"])


def collect_from_source_urls(path: Path, records: dict[str, dict], discovered_at: str) -> None:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")
        return
    for url in extract_urls(path.read_text(encoding="utf-8", errors="replace")):
        add_url(records, url, "source_urls_txt", discovered_at)


def collect_from_manual_sources(path: Path, records: dict[str, dict], discovered_at: str) -> None:
    path.mkdir(parents=True, exist_ok=True)
    for file_path in sorted(path.rglob("*")):
        if file_path.is_file() and file_path.name != ".gitkeep":
            text = file_path.read_text(encoding="utf-8", errors="replace")
            for url in extract_urls(text):
                add_url(records, url, "manual_sources", discovered_at)


def collect_from_previous(output_dir: Path, records: dict[str, dict], discovered_at: str) -> None:
    for article in read_json(output_dir / "articles.json", []):
        url = article.get("url")
        if url and ARTICLE_RE.fullmatch(url):
            add_url(records, url, "previous_articles", discovered_at)
    for failed in read_json(output_dir / "failed_urls.json", []):
        url = failed.get("url")
        if url and ARTICLE_RE.fullmatch(url):
            add_url(records, url, "previous_failed", discovered_at)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="data/ameblo")
    parser.add_argument("--source-urls", default="data/ameblo/source_urls.txt")
    parser.add_argument("--manual-sources", default="data/ameblo/manual_sources")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    discovered_at = now_iso()
    records: dict[str, dict] = {}

    collect_from_source_urls(Path(args.source_urls), records, discovered_at)
    collect_from_manual_sources(Path(args.manual_sources), records, discovered_at)
    collect_from_previous(output_dir, records, discovered_at)

    discovered = sorted(records.values(), key=lambda item: item["url"])
    write_json(output_dir / "discovered_urls.json", discovered)
    print(f"Discovered URL candidates: {len(discovered)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
