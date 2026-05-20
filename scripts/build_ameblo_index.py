#!/usr/bin/env python3
"""Build a taxonomy and target-section index from fetched Ameblo articles."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
import time


TARGET_SECTIONS = [
    "policy_coach_mindset",
    "policy_player_mindset",
    "policy_coach_assignment",
    "practice_flow",
    "practice_warmup",
    "practice_two_point_catchball",
    "practice_four_point_catchball",
    "practice_batting",
    "other",
]


TARGET_HINTS = {
    "practice_batting": {
        "categories": {"batting": 3},
        "keywords": ["バッティング", "スイング", "重心移動", "強い打球", "ホームラン", "打撃は結果で判断しない", "前足のブレーキ", "打つ準備"],
    },
    "practice_two_point_catchball": {
        "categories": {"defense": 2},
        "keywords": ["キャッチボール", "スローイング", "送球", "捕球", "持ち替え", "安定した送球"],
    },
    "practice_four_point_catchball": {
        "categories": {"defense": 2, "rules": 1},
        "keywords": ["4箇所", "４箇所", "ボール2個", "ランダム", "送球", "捕球", "ランダウンプレー"],
    },
    "practice_warmup": {
        "categories": {"body_mobility": 3, "athletic_base": 3, "defense": 1, "pitching": 1},
        "keywords": ["ストレッチ", "姿勢", "肩甲骨", "股関節", "体幹", "ビジョントレーニング", "スポーツをするための土台", "全身筋肉体幹", "スローイングの下地"],
    },
    "policy_coach_mindset": {
        "categories": {"coaching_method": 3, "mindset": 1},
        "keywords": ["コーチ", "指導", "指導方法", "育成", "見る", "伝える", "質", "成長", "評価", "原因を見る", "目的を伝える"],
    },
    "policy_player_mindset": {
        "categories": {"mindset": 3},
        "keywords": ["挨拶", "返事", "話を聞く", "継続", "やるかやらないか", "仲間", "もったいない", "ベンチでの過ごし方", "意識", "姿勢"],
    },
    "practice_flow": {
        "categories": {"coaching_method": 1, "mindset": 1, "rules": 1, "tactics": 1},
        "keywords": ["練習", "順番", "順序", "MTM", "ロコモ", "練習設計", "実戦", "試合", "課題"],
    },
    "policy_coach_assignment": {
        "categories": {"coaching_method": 2},
        "keywords": ["コーチ配置", "監督", "ヘッドコーチ", "グループ", "担当", "運営"],
    },
}


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def read_json(path: Path, default):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def count_keyword(text: str, keyword: str, cap: int = 5) -> int:
    if not keyword:
        return 0
    return min(text.count(keyword), cap)


def classify_source_categories(article: dict, taxonomy: dict) -> tuple[list[str], dict, list[dict], int]:
    title = article.get("title", "")
    body = article.get("body_text", "")
    source_scores: dict[str, int] = {}
    matched: list[dict] = []
    total_matches = 0

    for category in taxonomy.get("categories", []):
        score = 0
        label = category["label"]
        category_matches = []
        for keyword in category.get("keywords", []):
            title_hits = count_keyword(title, keyword, cap=3)
            body_hits = count_keyword(body, keyword, cap=5)
            if title_hits or body_hits:
                keyword_score = title_hits * 5 + body_hits
                score += keyword_score
                total_matches += title_hits + body_hits
                category_matches.append({
                    "keyword": keyword,
                    "title_hits": title_hits,
                    "body_hits": body_hits,
                    "score": keyword_score,
                })
        if score:
            source_scores[label] = score
            matched.extend({"category": label, **item} for item in category_matches)

    source_categories = [label for label, _ in sorted(source_scores.items(), key=lambda item: item[1], reverse=True)]
    return source_categories, source_scores, matched, total_matches


def score_targets(article: dict, source_scores_by_id: dict[str, int], matched_keywords: list[dict]) -> dict[str, int]:
    text = f"{article.get('title', '')}\n{article.get('body_text', '')}"
    scores = defaultdict(int)
    keyword_set = {item["keyword"] for item in matched_keywords}

    for target, hints in TARGET_HINTS.items():
        for category_id, weight in hints.get("categories", {}).items():
            if category_id in source_scores_by_id:
                scores[target] += min(source_scores_by_id[category_id], 20) * weight
        for keyword in hints.get("keywords", []):
            hits = count_keyword(text, keyword, cap=5)
            if hits:
                scores[target] += hits * (5 if keyword in article.get("title", "") else 2)

    # Case/tactics articles are useful, but usually not for direct current copy.
    if source_scores_by_id.get("tactics", 0) and not scores:
        scores["other"] += source_scores_by_id["tactics"]

    if not scores:
        scores["other"] = 1 if keyword_set else 0
    return dict(sorted(scores.items(), key=lambda item: item[1], reverse=True))


def recommended_use(target_scores: dict[str, int], source_scores: dict[str, int], article: dict) -> str:
    if not target_scores or max(target_scores.values()) <= 0:
        return "not_use"
    top_score = max(target_scores.values())
    body_length = len(article.get("body_text", ""))
    if top_score >= 20 and body_length >= 300:
        return "summary_source"
    if top_score >= 8:
        return "reference_link"
    if source_scores:
        return "background_only"
    return "not_use"


def notes_for(use: str, target_scores: dict[str, int]) -> str:
    if use == "summary_source":
        return "Strong candidate for future rewritten explanation; avoid long verbatim copying."
    if use == "reference_link":
        return "Candidate for future visible reference link after owner review."
    if use == "background_only":
        return "Use as background context; relevance is indirect or broad."
    return "No clear fit for current priority sections."


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/ameblo/articles.json")
    parser.add_argument("--taxonomy", default="data/ameblo/keyword_taxonomy.json")
    parser.add_argument("--output", default="data/ameblo/article_index.json")
    args = parser.parse_args()

    articles = read_json(Path(args.input), [])
    taxonomy = read_json(Path(args.taxonomy), {"categories": []})
    label_to_id = {cat["label"]: cat["id"] for cat in taxonomy.get("categories", [])}
    indexed = []

    for article in articles:
        source_categories, source_scores_by_label, matched_keywords, keyword_match_count = classify_source_categories(article, taxonomy)
        source_scores_by_id = {label_to_id[label]: score for label, score in source_scores_by_label.items() if label in label_to_id}
        target_scores = score_targets(article, source_scores_by_id, matched_keywords)
        target_sections = [name for name, score in target_scores.items() if score > 0]
        if not target_sections:
            target_sections = ["other"]
        use = recommended_use(target_scores, source_scores_by_label, article)
        indexed.append({
            "url": article.get("url", ""),
            "canonical_url": article.get("canonical_url", ""),
            "title": article.get("title", ""),
            "date": article.get("date", ""),
            "excerpt": article.get("body_excerpt", ""),
            "body_length": len(article.get("body_text", "")),
            "source_categories": source_categories,
            "matched_keywords": matched_keywords,
            "keyword_match_count": keyword_match_count,
            "relevance_score_by_source_category": source_scores_by_label,
            "target_sections": target_sections,
            "relevance_score_by_target_section": target_scores,
            "recommended_use": use,
            "notes": notes_for(use, target_scores),
        })

    indexed.sort(key=lambda item: max(item["relevance_score_by_target_section"].values() or [0]), reverse=True)
    output = {
        "generated_at": now_iso(),
        "article_count": len(indexed),
        "target_sections": TARGET_SECTIONS,
        "articles": indexed,
    }
    write_json(Path(args.output), output)
    print(f"Indexed: {len(indexed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
