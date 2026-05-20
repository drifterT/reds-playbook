#!/usr/bin/env python3
"""Build lightweight Playbook Text candidate themes from parsed Ameblo metadata."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

from ameblo_ingest_common import now_iso, read_json, write_json


THEME_RULES = {
    "defense_catchball": {
        "label": "守備・キャッチボール候補",
        "keywords": ["守備", "キャッチボール", "捕球", "送球", "スローイング", "カバー", "ランダウン", "タッグ"],
    },
    "batting": {
        "label": "バッティング候補",
        "keywords": ["バッティング", "打撃", "スイング", "打つ準備", "強い打球", "トップ"],
    },
    "baserunning": {
        "label": "走塁候補",
        "keywords": ["走塁", "スタート", "スライディング", "ランナー", "次の塁"],
    },
    "coaching_method": {
        "label": "指導方法候補",
        "keywords": ["指導", "コーチ", "育成", "見る", "伝える", "練習設計", "評価"],
    },
    "body_mobility": {
        "label": "身体構造・ストレッチ候補",
        "keywords": ["姿勢", "ストレッチ", "肩甲骨", "股関節", "体幹", "アフターケア"],
    },
}


def article_keywords(article: dict) -> set[str]:
    return {item.get("keyword", "") for item in article.get("detected_keywords", []) if item.get("keyword")}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parsed-dir", default="data/ameblo/parsed_articles")
    parser.add_argument("--output", default="data/playbook-text/discovery/theme-candidates.json")
    parser.add_argument("--summary", default="docs/playbook-text/discovery-summary.md")
    args = parser.parse_args()

    parsed_dir = Path(args.parsed_dir)
    parsed_dir.mkdir(parents=True, exist_ok=True)
    articles = []
    for path in sorted(parsed_dir.glob("*.json")):
        articles.append(read_json(path, {}))

    themes = []
    for theme_key, rule in THEME_RULES.items():
        matched_urls = []
        matched_keywords = defaultdict(int)
        phrases = []
        for article in articles:
            keywords = article_keywords(article)
            direct = keywords.intersection(rule["keywords"])
            text_blob = " ".join([
                article.get("title", ""),
                article.get("summary_for_internal_review", ""),
                article.get("content_excerpt_for_review", ""),
            ])
            indirect = {kw for kw in rule["keywords"] if kw in text_blob}
            hits = direct.union(indirect)
            if not hits:
                continue
            matched_urls.append(article.get("url", ""))
            for keyword in hits:
                matched_keywords[keyword] += 1
            phrases.extend(article.get("candidate_phrases", [])[:3])
        themes.append({
            "theme_key": theme_key,
            "label": rule["label"],
            "matched_article_urls": sorted(set(url for url in matched_urls if url)),
            "matched_keywords": [
                {"keyword": key, "count": count}
                for key, count in sorted(matched_keywords.items(), key=lambda item: item[1], reverse=True)
            ],
            "candidate_phrases": sorted(set(phrases))[:12],
            "needs_ai_review": True,
        })

    output = {
        "generated_at": now_iso(),
        "article_count": len(articles),
        "themes": themes,
        "source_policy": {
            "stores_full_text": False,
            "uses_short_excerpt_and_metadata": True,
        },
    }
    write_json(Path(args.output), output)

    lines = [
        "# Ameblo Theme Discovery Summary",
        "",
        f"Generated at: {output['generated_at']}",
        "",
        f"Parsed articles: {len(articles)}",
        "",
        "This summary uses URL, metadata, short excerpts, detected keywords, and candidate phrases only. It does not store full Ameblo article text.",
        "",
    ]
    for theme in themes:
        lines.append(f"## {theme['label']}")
        lines.append("")
        lines.append(f"- Matched articles: {len(theme['matched_article_urls'])}")
        if theme["matched_article_urls"]:
            lines.append("- URLs:")
            for url in theme["matched_article_urls"][:10]:
                lines.append(f"  - {url}")
        if theme["matched_keywords"]:
            keywords = ", ".join(item["keyword"] for item in theme["matched_keywords"][:10])
            lines.append(f"- Matched keywords: {keywords}")
        lines.append("- Needs AI review: yes")
        lines.append("")
    Path(args.summary).parent.mkdir(parents=True, exist_ok=True)
    Path(args.summary).write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"Parsed articles: {len(articles)}")
    print(f"Wrote: {args.output}")
    print(f"Wrote: {args.summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
