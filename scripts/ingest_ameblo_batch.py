#!/usr/bin/env python3
"""Fetch a small batch of pending Ameblo article URLs from approved themes."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import time

from ameblo_ingest_common import (
    can_fetch,
    candidate_phrases,
    clean_extracted_text,
    detect_keywords,
    entry_id,
    fetch_url,
    load_keywords,
    load_robots,
    now_iso,
    published_at_from_html,
    read_json,
    short_text,
    text_from_html,
    title_from_html,
    write_json,
)


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


def parsed_record(item: dict, html_text: str, raw_path: Path, parsed_path: Path, taxonomy_path: Path) -> dict:
    text = text_from_html(html_text)
    keywords_by_category = load_keywords(taxonomy_path)
    detected = detect_keywords(text, keywords_by_category)
    phrases = candidate_phrases(text, detected)
    keyword_labels = [entry["keyword"] for entry in detected[:12]]
    summary = " / ".join(keyword_labels[:8])
    if summary:
        summary = f"検出キーワード: {summary}"
    else:
        summary = "検出キーワードなし。AIレビューまたは手動確認が必要。"
    return {
        "url": item["url"],
        "entry_id": entry_id(item["url"]),
        "theme_id": item["theme_id"],
        "theme_label": item["theme_label"],
        "title": title_from_html(html_text),
        "published_at": published_at_from_html(html_text),
        "fetched_at": now_iso(),
        "status": "fetched",
        "text_length": len(text),
        "content_excerpt_for_review": short_text(text, 120),
        "detected_keywords": detected,
        "candidate_phrases": phrases,
        "summary_for_internal_review": summary,
        "raw_path": str(raw_path),
        "parsed_path": str(parsed_path),
        "content_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "source_policy": {
            "public_republish_allowed": False,
            "store_full_text_in_repo": False,
            "use_for_internal_theme_discovery": True,
        },
    }


def reprocess_existing_records(state: dict, raw_dir: Path, parsed_dir: Path, taxonomy_path: Path, limit: int) -> int:
    processed = list(state.get("processed_urls", {}).values())
    count = 0
    for item in processed[:limit]:
        raw_path = Path(item.get("raw_path") or raw_dir / f"{entry_id(item['url'])}.html")
        if not raw_path.exists():
            continue
        parsed_path = Path(item.get("parsed_path") or parsed_dir / f"{entry_id(item['url'])}.json")
        html_text = raw_path.read_text(encoding="utf-8", errors="replace")
        write_json(parsed_path, parsed_record(item, html_text, raw_path, parsed_path, taxonomy_path))
        count += 1
    return count


def repair_existing_records(parsed_dir: Path, taxonomy_path: Path) -> int:
    keywords_by_category = load_keywords(taxonomy_path)
    count = 0
    for path in sorted(parsed_dir.glob("*.json")):
        record = read_json(path, {})
        old_excerpt = record.get("content_excerpt_for_review", "")
        old_phrases = "\n".join(record.get("candidate_phrases", []))
        cleaned_source = clean_extracted_text(f"{old_excerpt}\n{old_phrases}", record.get("title", ""))
        if not cleaned_source:
            cleaned_source = record.get("title", "").strip()
        classification_source = f"{record.get('title', '')}\n{cleaned_source}"
        detected = detect_keywords(classification_source, keywords_by_category)
        record["content_excerpt_for_review"] = short_text(cleaned_source, 120)
        record["detected_keywords"] = detected
        record["candidate_phrases"] = candidate_phrases(classification_source, detected)
        record["summary_for_internal_review"] = (
            "検出キーワード: " + " / ".join(item["keyword"] for item in detected[:8])
            if detected
            else "検出キーワードなし。AIレビューまたは手動確認が必要。"
        )
        record.setdefault("source_policy", {})["store_full_text_in_repo"] = False
        record["repaired_without_raw_html"] = True
        write_json(path, record)
        count += 1
    return count


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", default="data/ameblo/ingestion_state.json")
    parser.add_argument("--raw-dir", default="data/ameblo/raw_articles")
    parser.add_argument("--parsed-dir", default="data/ameblo/parsed_articles")
    parser.add_argument("--log-dir", default="data/ameblo/ingestion_logs")
    parser.add_argument("--taxonomy", default="data/ameblo/keyword_taxonomy.json")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--delay-seconds", type=float, default=2.0)
    parser.add_argument("--reprocess-existing", action="store_true")
    parser.add_argument("--repair-existing-parsed", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    state_path = Path(args.state)
    state = read_json(state_path, default_state())
    max_per_run = int(state.get("max_articles_per_run") or 10)
    limit = max(0, min(args.limit, max_per_run))
    pending = list(state.get("pending_urls", []))
    batch = pending[:limit]

    if args.dry_run:
        print(f"Dry run: pending={len(pending)}, limit={limit}, would_process={len(batch)}")
        if args.reprocess_existing:
            raw_dir = Path(args.raw_dir)
            raw_count = 0
            for item in list(state.get("processed_urls", {}).values())[:limit]:
                raw_path = Path(item.get("raw_path") or raw_dir / f"{entry_id(item['url'])}.html")
                if raw_path.exists():
                    raw_count += 1
            print(f"Dry run: would reprocess existing records with raw HTML: {raw_count}")
        if args.repair_existing_parsed:
            parsed_count = len(list(Path(args.parsed_dir).glob("*.json")))
            print(f"Dry run: would repair existing parsed JSON records without raw HTML: {parsed_count}")
        for item in batch:
            print(f"- {item.get('url')} ({item.get('theme_label')})")
        print("No network fetch or state update performed.")
        return 0

    raw_dir = Path(args.raw_dir)
    parsed_dir = Path(args.parsed_dir)
    log_dir = Path(args.log_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    parsed_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    if args.reprocess_existing:
        count = reprocess_existing_records(state, raw_dir, parsed_dir, Path(args.taxonomy), limit)
        print(f"Reprocessed existing parsed records from raw HTML: {count}")
        return 0
    if args.repair_existing_parsed:
        count = repair_existing_records(parsed_dir, Path(args.taxonomy))
        print(f"Repaired existing parsed JSON records without raw HTML: {count}")
        return 0
    robots = load_robots()
    processed = state.setdefault("processed_urls", {})
    blocked = state.setdefault("blocked_urls", [])
    failed = state.setdefault("failed_urls", [])
    remaining = pending[limit:]
    log_entries: list[dict] = []

    for item in batch:
        timestamp = now_iso()
        item["attempt_count"] = int(item.get("attempt_count") or 0) + 1
        item["last_attempt_at"] = timestamp
        url = item["url"]
        if not can_fetch(robots, url):
            blocked_item = {
                **item,
                "status": "blocked",
                "stage": "fetch",
                "error": "blocked_by_robots",
            }
            blocked.append(blocked_item)
            log_entries.append(blocked_item)
            continue
        status, html_text, err = fetch_url(url)
        if err or status >= 400 or not html_text:
            failed_item = {
                **item,
                "status": "failed",
                "stage": "fetch",
                "http_status": status,
                "error": err or f"HTTP status {status}",
            }
            failed.append(failed_item)
            log_entries.append(failed_item)
            continue
        eid = entry_id(url)
        raw_path = raw_dir / f"{eid}.html"
        parsed_path = parsed_dir / f"{eid}.json"
        raw_path.write_text(html_text, encoding="utf-8")
        record = parsed_record(item, html_text, raw_path, parsed_path, Path(args.taxonomy))
        write_json(parsed_path, record)
        processed[url] = {
            **item,
            "status": "fetched",
            "last_attempt_at": record["fetched_at"],
            "raw_path": str(raw_path),
            "parsed_path": str(parsed_path),
            "error": None,
        }
        log_entries.append(processed[url])
        time.sleep(args.delay_seconds)

    state["pending_urls"] = remaining
    state["last_run_at"] = now_iso()
    write_json(state_path, state)
    log_path = log_dir / f"{state['last_run_at'][:10]}.json"
    existing_log = read_json(log_path, [])
    write_json(log_path, existing_log + log_entries)
    print(f"Processed batch size: {len(batch)}")
    print(f"Fetched: {sum(1 for item in log_entries if item.get('status') == 'fetched')}")
    print(f"Blocked: {sum(1 for item in log_entries if item.get('status') == 'blocked')}")
    print(f"Failed: {sum(1 for item in log_entries if item.get('status') == 'failed')}")
    print(f"Remaining pending: {len(remaining)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
