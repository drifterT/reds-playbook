#!/usr/bin/env python3
"""Shared helpers for the theme-limited Ameblo ingestion pipeline."""

from __future__ import annotations

import hashlib
from html.parser import HTMLParser
import html
import json
from pathlib import Path
import re
import time
from urllib import error, parse, request, robotparser


BLOG_ROOT = "https://ameblo.jp/kinegawareds/"
ROBOTS_URL = "https://ameblo.jp/robots.txt"
USER_AGENT = "reds-playbook-theme-ingestor/0.1 (+https://github.com/drifterT/reds-playbook)"
ARTICLE_RE = re.compile(r"https://ameblo\.jp/kinegawareds/entry-\d+\.html")
THEME_RE = re.compile(r"https://ameblo\.jp/kinegawareds/theme-\d+\.html")
ARTICLE_BODY_MARKERS = (
    "entrybody",
    "skin-entrybody",
    "articletext",
    "article-text",
    "entry-text",
    "article-body",
    "js-entrybody",
)
UI_NOISE_TERMS = (
    "ホーム",
    "ピグ",
    "アメブロ",
    "芸能人ブログ",
    "人気ブログ",
    "新規登録",
    "ログイン",
    "夢に向かって！木根川レッズ",
    "葛飾区少年軟式野球連盟所属",
    "公式ブログ",
    "ブログトップ",
    "記事一覧",
    "画像一覧",
    "コメントする",
    "リブログする",
    "このブログをフォローする",
)


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def read_json(path: Path, default):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_url(href: str, base: str) -> str:
    absolute = parse.urljoin(base, html.unescape(href.strip()))
    parts = parse.urlsplit(absolute)
    return parse.urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def entry_id(url: str) -> str:
    match = re.search(r"entry-(\d+)\.html", url)
    if match:
        return f"entry-{match.group(1)}"
    return "entry-" + hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]


def load_robots() -> robotparser.RobotFileParser:
    robots = robotparser.RobotFileParser()
    robots.set_url(ROBOTS_URL)
    try:
        robots.read()
    except Exception:
        pass
    return robots


def can_fetch(robots: robotparser.RobotFileParser, url: str) -> bool:
    try:
        return robots.can_fetch(USER_AGENT, url)
    except Exception:
        return True


def fetch_url(url: str, timeout: int = 20) -> tuple[int, str, str | None]:
    req = request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            body = resp.read().decode(charset, errors="replace")
            return resp.status, body, None
    except error.HTTPError as exc:
        return exc.code, "", f"HTTPError: {exc.code} {exc.reason}"
    except error.URLError as exc:
        return 0, "", f"URLError: {exc.reason}"
    except Exception as exc:
        return 0, "", f"{type(exc).__name__}: {exc}"


class PageTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in {"script", "style", "noscript", "svg"}:
            self.skip_depth += 1
        if tag in {"p", "br", "li", "div", "section", "article", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg"} and self.skip_depth:
            self.skip_depth -= 1
        if tag in {"p", "li", "div", "section", "article"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        text = data.strip()
        if text:
            self.parts.append(text)

    def text(self) -> str:
        joined = html.unescape(" ".join(self.parts))
        lines = [re.sub(r"\s+", " ", line).strip() for line in joined.splitlines()]
        return "\n".join(line for line in lines if line and line not in UI_NOISE_TERMS)


class ArticleBodyExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.candidates: list[str] = []
        self.current: list[str] | None = None
        self.capture_depth = 0
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        attr_text = " ".join(str(value).lower() for _key, value in attrs if value)
        is_body_marker = tag == "article" or any(marker in attr_text for marker in ARTICLE_BODY_MARKERS)
        if is_body_marker and self.capture_depth == 0:
            self.current = []
            self.capture_depth = 1
        elif self.capture_depth:
            self.capture_depth += 1

        if self.capture_depth and tag in {"script", "style", "noscript", "svg"}:
            self.skip_depth += 1
        if self.capture_depth and tag in {"p", "br", "li", "div", "section", "article", "h1", "h2", "h3"}:
            self.current_append("\n")

    def handle_endtag(self, tag: str) -> None:
        if self.capture_depth and tag in {"script", "style", "noscript", "svg"} and self.skip_depth:
            self.skip_depth -= 1
        if self.capture_depth and tag in {"p", "li", "div", "section", "article"}:
            self.current_append("\n")
        if self.capture_depth:
            self.capture_depth -= 1
            if self.capture_depth == 0 and self.current is not None:
                text = self.clean_join(self.current)
                if text:
                    self.candidates.append(text)
                self.current = None

    def handle_data(self, data: str) -> None:
        if not self.capture_depth or self.skip_depth:
            return
        text = data.strip()
        if text:
            self.current_append(text)

    def current_append(self, value: str) -> None:
        if self.current is not None:
            self.current.append(value)

    @staticmethod
    def clean_join(parts: list[str]) -> str:
        joined = html.unescape(" ".join(parts))
        lines = [re.sub(r"\s+", " ", line).strip() for line in joined.splitlines()]
        return "\n".join(line for line in lines if line and line not in UI_NOISE_TERMS)


def text_from_html(html_text: str) -> str:
    article_parser = ArticleBodyExtractor()
    article_parser.feed(html_text)
    candidates = [clean_extracted_text(text) for text in article_parser.candidates]
    candidates = [text for text in candidates if len(text) >= 40]
    if candidates:
        return max(candidates, key=len)

    parser = PageTextExtractor()
    parser.feed(html_text)
    return clean_extracted_text(parser.text(), title_from_html(html_text))


def meta_value(html_text: str, *names: str) -> str:
    wanted = {name.lower() for name in names}
    for match in re.finditer(r"<meta\s+([^>]+)>", html_text, re.I):
        attrs = {
            key.lower(): value
            for key, value in re.findall(r"""([a-zA-Z_:.-]+)=["']([^"']*)["']""", match.group(1))
        }
        key = (attrs.get("property") or attrs.get("name") or "").lower()
        if key in wanted:
            return html.unescape(attrs.get("content", "")).strip()
    return ""


def title_from_html(html_text: str) -> str:
    title = meta_value(html_text, "og:title", "twitter:title")
    if title:
        return title
    match = re.search(r"<title[^>]*>(.*?)</title>", html_text, re.I | re.S)
    if not match:
        return ""
    return re.sub(r"\s+", " ", html.unescape(match.group(1))).strip()


def clean_extracted_text(text: str, title: str = "") -> str:
    clean = html.unescape(text)
    for term in UI_NOISE_TERMS:
        clean = clean.replace(term, " ")
    if title:
        title_only = re.sub(r"\s*\|.*$", "", title).strip()
        title_plain = title_only.strip("「」『』")
        for title_variant in (title, title_only, title_plain):
            if title_variant:
                clean = clean.replace(title_variant, " ")
    clean = re.sub(r"木根川レッズ[（(]\s*[）)]", " ", clean)
    clean = re.sub(r"木根川レッズ[（(][^）)]*[）)]", " ", clean)
    clean = re.sub(r"[（(]\s*[）)]", " ", clean)
    clean = re.sub(r"\s*\|\s*", " ", clean)
    clean = re.sub(r"『[^』]*野球体験会のご案内[^。]*", " ", clean)
    clean = re.sub(r"「カラーバット[^。]*", " ", clean)
    clean = re.sub(r"(ブログ|トップ|フォロー|ランキング|プロフィール)\s*", " ", clean)
    clean = re.sub(r"(?:(?<=\s)|^)(公式ブ|公|トッ|ト|カッ)(?=\s|$)", " ", clean)
    for _ in range(4):
        clean = re.sub(r"(.{8,120}?)\s+\1", r"\1", clean)
    lines = [re.sub(r"\s+", " ", line).strip(" .　") for line in clean.splitlines()]
    lines = [line for line in lines if line and line not in UI_NOISE_TERMS]
    return "\n".join(lines)


def published_at_from_html(html_text: str) -> str | None:
    value = meta_value(html_text, "article:published_time", "date", "pubdate")
    if value:
        return value
    match = re.search(r"(\d{4})[./-](\d{1,2})[./-](\d{1,2})", html_text)
    if match:
        y, m, d = match.groups()
        return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"
    return None


def short_text(text: str, limit: int = 120) -> str:
    clean = re.sub(r"\s+", " ", text).strip()
    if len(clean) <= limit:
        return clean
    return clean[:limit].rstrip() + "..."


def load_keywords(taxonomy_path: Path) -> dict[str, list[str]]:
    taxonomy = read_json(taxonomy_path, {"categories": []})
    result: dict[str, list[str]] = {}
    for category in taxonomy.get("categories", []):
        label = category.get("label") or category.get("id") or "unknown"
        result[label] = [kw for kw in category.get("keywords", []) if kw]
    return result


def detect_keywords(text: str, keywords_by_category: dict[str, list[str]], cap: int = 40) -> list[dict]:
    matches: list[dict] = []
    for category, keywords in keywords_by_category.items():
        for keyword in keywords:
            count = text.count(keyword)
            if count:
                matches.append({"category": category, "keyword": keyword, "count": min(count, 10)})
    matches.sort(key=lambda item: (item["count"], len(item["keyword"])), reverse=True)
    return matches[:cap]


def candidate_phrases(text: str, matched_keywords: list[dict], cap: int = 8) -> list[str]:
    if not matched_keywords:
        return []
    keywords = [item["keyword"] for item in matched_keywords[:12]]
    raw_sentences = re.split(r"[。\n]", text)
    phrases: list[str] = []
    for sentence in raw_sentences:
        clean = re.sub(r"\s+", " ", sentence).strip()
        if not clean:
            continue
        if any(keyword in clean for keyword in keywords):
            phrases.append(short_text(clean, 70))
        if len(phrases) >= cap:
            break
    return phrases
