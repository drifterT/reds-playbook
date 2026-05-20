#!/usr/bin/env python3
"""Generate a planning document mapping Ameblo articles to playbook sections."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import time


SECTION_ORDER = [
    ("policy_coach_mindset", "方針・心得", "コーチ心得", "Practice and coaching principles for adults."),
    ("policy_player_mindset", "方針・心得", "選手心得", "Player behavior and mindset guidance."),
    ("policy_coach_assignment", "方針・心得", "コーチ配置", "Operational assignment of coaches. Treat current notes as owner-provided policy."),
    ("practice_flow", "レギュラー練習メニュー", "練習の流れ", "Standard sequence and rationale for practice blocks."),
    ("practice_warmup", "レギュラー練習メニュー", "アップ", "Warmup, movement foundation, throwing foundation, and body preparation."),
    ("practice_two_point_catchball", "レギュラー練習メニュー", "2箇所キャッチボール", "Catchball structure and quick catch-to-throw repetitions."),
    ("practice_four_point_catchball", "レギュラー練習メニュー", "4箇所キャッチボール", "Four-station throw/catch structure and multi-ball decision practice."),
    ("practice_batting", "レギュラー練習メニュー", "バッティング練習", "Batting practice structure and related hitting concepts."),
]

RECOMMENDED_ORDER = [
    "方針・心得 > コーチ心得",
    "レギュラー練習メニュー > 練習の流れ",
    "レギュラー練習メニュー > アップ",
    "レギュラー練習メニュー > バッティング練習",
    "レギュラー練習メニュー > 2箇所キャッチボール",
    "レギュラー練習メニュー > 4箇所キャッチボール",
    "方針・心得 > 選手心得",
    "方針・心得 > コーチ配置",
]


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def read_json(path: Path, default):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


def md_escape(text: str) -> str:
    return (text or "").replace("\n", " ").strip()


def article_link(article: dict) -> str:
    title = md_escape(article.get("title")) or article.get("url", "Untitled")
    url = article.get("url", "")
    if not url:
        return title
    return f"[{title}]({url})"


def keywords(article: dict, limit: int = 12) -> list[str]:
    seen = []
    for item in article.get("matched_keywords", []):
        kw = item.get("keyword")
        if kw and kw not in seen:
            seen.append(kw)
        if len(seen) >= limit:
            break
    return seen


def relevant_articles(articles: list[dict], section_id: str, limit: int = 8) -> list[dict]:
    chosen = [
        a for a in articles
        if section_id in a.get("target_sections", [])
        and a.get("recommended_use") != "not_use"
        and a.get("classification_status") == "classified"
    ]
    chosen.sort(key=lambda a: a.get("relevance_score_by_target_section", {}).get(section_id, 0), reverse=True)
    return chosen[:limit]


def render_article_bullets(articles: list[dict], section_id: str) -> list[str]:
    if not articles:
        return [
            "- Direct article support is weak or not fetched yet.",
            "- Treat current site notes as owner-provided content and mark detailed expansion as 要確認.",
        ]
    lines = []
    for article in articles:
        kws = keywords(article)
        lines.extend([
            f"- {article_link(article)}",
            f"  - URL: {article.get('url', '')}",
            f"  - Canonical URL: {article.get('canonical_url') or 'not captured'}",
            f"  - Date: {article.get('date') or 'not captured'}",
            f"  - Source categories: {', '.join(article.get('source_categories', [])) or 'none'}",
            f"  - Matched keywords: {', '.join(kws) or 'none'}",
            f"  - Use: {article.get('recommended_use', '')}",
            f"  - How to reflect in site: summarize concepts in practical Japanese after owner review; keep the source URL for possible 参考記事 links.",
        ])
    return lines


def render_section(section_id: str, group: str, label: str, purpose: str, articles: list[dict]) -> list[str]:
    related = relevant_articles(articles, section_id)
    lines = [
        f"### {label}",
        "",
        f"- Current purpose: {purpose}",
        "- Related Ameblo articles:",
        *render_article_bullets(related, section_id),
        "- Concepts to extract:",
        "  - Keep only practical concepts that help coaches and parents understand the section.",
        "  - Do not copy long text verbatim.",
        "  - Separate confirmed policy from interpretation.",
        "- Remaining questions / decisions:",
    ]
    if section_id == "policy_coach_assignment":
        lines.append("  - Direct blog support may be weak; treat current coach assignment notes as owner-provided policy.")
    elif section_id in {"practice_two_point_catchball", "practice_four_point_catchball", "practice_batting"}:
        lines.append("  - Detailed drill settings are still owner decisions and should remain 準備中 or 要確認 until reviewed.")
    else:
        lines.append("  - Owner review needed before converting this planning material into public copy.")
    lines.append("")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", default="data/ameblo/article_index.json")
    parser.add_argument("--articles", default="data/ameblo/articles.json")
    parser.add_argument("--fetch-log", default="data/ameblo/fetch_log.json")
    parser.add_argument("--failed", default="data/ameblo/failed_urls.json")
    parser.add_argument("--discovered", default="data/ameblo/discovered_urls.json")
    parser.add_argument("--output", default="docs/content-source-map.md")
    args = parser.parse_args()

    index = read_json(Path(args.index), {"articles": [], "article_count": 0})
    articles_raw = read_json(Path(args.articles), [])
    fetch_log = read_json(Path(args.fetch_log), {})
    failed = read_json(Path(args.failed), [])
    discovered = read_json(Path(args.discovered), [])
    articles = index.get("articles", [])
    status_counts = index.get("status_counts", {})
    blocked_count = status_counts.get("blocked_by_robots", 0)
    pending_count = status_counts.get("pending", 0)
    fetched_count = status_counts.get("fetched", 0) + status_counts.get("cached", 0)
    no_body = [article for article in articles if article.get("classification_status") != "classified"]

    high_priority = [
        article for article in articles
        if len([s for s in article.get("target_sections", []) if s != "other"]) >= 2
        and article.get("recommended_use") in {"summary_source", "reference_link"}
    ][:12]
    low_priority = [article for article in articles if article.get("recommended_use") == "not_use"][:8]

    lines = [
        "# Content Source Map",
        "",
        "## Purpose",
        "",
        "This document maps Ameblo source articles to future reds-playbook copy updates.",
        "It focuses first on レギュラー練習メニュー and 方針・心得.",
        "It is a planning document, not final public copy.",
        "Public HTML copy should be updated in later focused tasks.",
        "Source article URLs are preserved so future public pages can show 参考記事 links.",
        "",
        "## Source Processing Summary",
        "",
        f"- Discovered URL count: {len(discovered) or fetch_log.get('discovered_count', 0)}",
        f"- Fetched article count: {fetched_count or fetch_log.get('fetched_count', len(articles_raw))}",
        f"- Blocked by robots count: {blocked_count}",
        f"- Pending manual input count: {pending_count}",
        f"- Number of articles indexed: {index.get('article_count', len(articles))}",
        f"- Generation timestamp: {now_iso()}",
        f"- Fetch blockers or limitations: {len(failed)} failed/skipped URLs logged in `data/ameblo/failed_urls.json`.",
        "",
        "## 方針・心得",
        "",
    ]

    for section_id, group, label, purpose in SECTION_ORDER[:3]:
        lines.extend(render_section(section_id, group, label, purpose, articles))

    lines.extend(["## レギュラー練習メニュー", ""])
    for section_id, group, label, purpose in SECTION_ORDER[3:]:
        lines.extend(render_section(section_id, group, label, purpose, articles))

    lines.extend([
        "## High-priority Articles",
        "",
    ])
    if high_priority:
        for article in high_priority:
            lines.extend([
                f"- {article_link(article)}",
                f"  - URL: {article.get('url', '')}",
                f"  - Canonical URL: {article.get('canonical_url') or 'not captured'}",
                f"  - Date: {article.get('date') or 'not captured'}",
                f"  - Matched keywords: {', '.join(keywords(article)) or 'none'}",
                f"  - Target sections: {', '.join(article.get('target_sections', []))}",
                f"  - Use: {article.get('recommended_use', '')}",
                "  - Reason: High relevance across multiple target sections or strong section score.",
            ])
    else:
        lines.append("- No high-priority articles identified yet.")

    lines.extend([
        "",
        "## URL Status / Body Not Retrieved",
        "",
    ])
    if no_body:
        for article in no_body:
            lines.extend([
                f"- [{article.get('url')}]({article.get('url')})",
                f"  - Fetch status: {article.get('fetch_status')}",
                f"  - Classification status: {article.get('classification_status')}",
                f"  - Notes: {article.get('notes')}",
            ])
    else:
        lines.append("- No body-missing URLs currently recorded.")

    lines.extend([
        "",
        "## Do-not-use / Low Priority Articles",
        "",
    ])
    if low_priority:
        for article in low_priority:
            lines.append(f"- {article_link(article)} - no clear fit for current priority sections.")
    else:
        lines.append("- Unrelated, too personal, or unsuitable article types should be marked `not_use` during owner review.")

    lines.extend([
        "",
        "## Future Public Reference Design",
        "",
        "Future public pages may include a small section after owner review:",
        "",
        "```html",
        "<section class=\"references\">",
        "  <h3>参考記事</h3>",
        "  <ul>",
        "    <li><a href=\"https://ameblo.jp/kinegawareds/entry-xxxxx.html\" target=\"_blank\" rel=\"noopener\">記事タイトル</a></li>",
        "  </ul>",
        "</section>",
        "```",
        "",
        "Use source Ameblo URLs from `article_index.json` or this document. Do not link to local raw HTML cache paths.",
        "",
        "## Recommended Next Copy Update Order",
        "",
    ])
    lines.extend(f"{i}. {item}" for i, item in enumerate(RECOMMENDED_ORDER, 1))
    lines.extend([
        "",
        "## Editorial Rules for Future Copy",
        "",
        "- Do not copy long Ameblo text verbatim.",
        "- Summarize and reorganize in clear, practical Japanese.",
        "- Preserve team philosophy.",
        "- Make text easier for coaches and parents to understand.",
        "- Separate confirmed policy from interpretation.",
        "- Mark uncertain items as 要確認.",
        "- Do not include personal information about children.",
        "- Do not include raw passcodes or auth-related secrets.",
        "- Keep source URLs for attribution/reference.",
        "",
    ])

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
