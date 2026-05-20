#!/usr/bin/env python3
"""Fetch public Ameblo article pages for local content planning.

This script only accesses public pages, preserves source URLs, caches raw HTML,
and writes structured article records for later local indexing.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import time
from typing import Iterable
from urllib import error, parse, request, robotparser


BLOG_TOP = "https://ameblo.jp/kinegawareds/"
USER_AGENT = "reds-playbook-content-mapper/0.1 (+https://github.com/drifterT/reds-playbook)"
ARTICLE_RE = re.compile(r"https://ameblo\.jp/kinegawareds/entry-\d+\.html")
LINK_RE = re.compile(r"""href=["']([^"']+)["']""", re.I)
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
CANONICAL_RE = re.compile(r"""<link[^>]+rel=["']canonical["'][^>]+href=["']([^"']+)["']""", re.I)
META_RE = re.compile(r"""<meta\s+([^>]+)>""", re.I)


class TextExtractor(HTMLParser):
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
        if not self.skip_depth:
            text = data.strip()
            if text:
                self.parts.append(text)

    def text(self) -> str:
        joined = html.unescape(" ".join(self.parts))
        lines = [re.sub(r"\s+", " ", line).strip() for line in joined.splitlines()]
        return "\n".join(line for line in lines if line)


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def safe_name(url: str) -> str:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    match = re.search(r"entry-(\d+)\.html", url)
    if match:
        return f"entry-{match.group(1)}-{digest}.html"
    return f"page-{digest}.html"


def normalize_url(href: str, base: str) -> str:
    href = html.unescape(href.strip())
    absolute = parse.urljoin(base, href)
    clean = parse.urlsplit(absolute)
    return parse.urlunsplit((clean.scheme, clean.netloc, clean.path, "", ""))


def load_robots() -> robotparser.RobotFileParser:
    robots = robotparser.RobotFileParser()
    robots.set_url(parse.urljoin(BLOG_TOP, "/robots.txt"))
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
    req = request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"})
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


def discover_links(html_text: str, base_url: str) -> tuple[set[str], set[str]]:
    article_urls: set[str] = set()
    follow_urls: set[str] = set()
    for raw in LINK_RE.findall(html_text):
        url = normalize_url(raw, base_url)
        if ARTICLE_RE.match(url):
            article_urls.add(url)
        elif url.startswith(BLOG_TOP) and any(token in url for token in ("archive", "entrylist", "theme", "page-")):
            follow_urls.add(url)
    return article_urls, follow_urls


def meta_value(html_text: str, *names: str) -> str:
    names_l = {name.lower() for name in names}
    for match in META_RE.finditer(html_text):
        tag = match.group(1)
        attrs = dict((k.lower(), v) for k, v in re.findall(r"""([a-zA-Z_:.-]+)=["']([^"']*)["']""", tag))
        key = (attrs.get("property") or attrs.get("name") or "").lower()
        if key in names_l:
            return html.unescape(attrs.get("content", "")).strip()
    return ""


def title_from_html(html_text: str) -> str:
    og_title = meta_value(html_text, "og:title", "twitter:title")
    if og_title:
        return og_title
    match = TITLE_RE.search(html_text)
    if not match:
        return ""
    return re.sub(r"\s+", " ", html.unescape(match.group(1))).strip()


def canonical_from_html(html_text: str, fallback: str) -> str:
    match = CANONICAL_RE.search(html_text)
    if match:
        return normalize_url(match.group(1), fallback)
    og_url = meta_value(html_text, "og:url")
    if og_url:
        return normalize_url(og_url, fallback)
    return fallback


def date_from_html(html_text: str) -> str:
    value = meta_value(html_text, "article:published_time", "date", "pubdate")
    if value:
        return value[:10]
    match = re.search(r"(\d{4})[./-](\d{1,2})[./-](\d{1,2})", html_text)
    if match:
        y, m, d = match.groups()
        return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"
    return ""


def body_text_from_html(html_text: str) -> str:
    candidates = []
    for pattern in (
        r"<article[\s\S]*?</article>",
        r"<div[^>]+(?:entryBody|skin-entryBody|articleText|js-entryBody)[^>]*>[\s\S]*?</div>",
        r"<body[\s\S]*?</body>",
    ):
        match = re.search(pattern, html_text, re.I)
        if match:
            candidates.append(match.group(0))
    source = max(candidates, key=len) if candidates else html_text
    extractor = TextExtractor()
    extractor.feed(source)
    text = extractor.text()
    noise = ("このブログをフォローする", "記事一覧", "画像一覧", "コメントする", "リブログする")
    lines = [line for line in text.splitlines() if line not in noise]
    return "\n".join(lines)


def excerpt(text: str, limit: int = 180) -> str:
    clean = re.sub(r"\s+", " ", text).strip()
    return clean[:limit] + ("..." if len(clean) > limit else "")


def article_id(url: str) -> str:
    match = re.search(r"entry-(\d+)\.html", url)
    return match.group(1) if match else hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]


def read_json(path: Path, default):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, articles: list[dict]) -> None:
    fields = ["url", "canonical_url", "title", "date", "body_excerpt", "fetched_at", "source_html_path"]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for article in articles:
            writer.writerow({field: article.get(field, "") for field in fields})


def discover_article_urls(max_articles: int, delay: float, output_dir: Path, refresh: bool, robots) -> tuple[list[str], list[dict]]:
    discovered: set[str] = set()
    failed: list[dict] = []
    queue = [BLOG_TOP]
    seen_pages: set[str] = set()
    max_listing_pages = 20

    while queue and len(discovered) < max_articles and len(seen_pages) < max_listing_pages:
        page_url = queue.pop(0)
        if page_url in seen_pages:
            continue
        seen_pages.add(page_url)
        if not can_fetch(robots, page_url):
            failed.append({"url": page_url, "stage": "discover", "error": "blocked_by_robots"})
            continue
        status, body, err = fetch_url(page_url)
        if err or status >= 400:
            failed.append({"url": page_url, "stage": "discover", "status": status, "error": err})
            continue
        articles, follow = discover_links(body, page_url)
        discovered.update(articles)
        for follow_url in sorted(follow):
            if follow_url not in seen_pages and follow_url not in queue:
                queue.append(follow_url)
        time.sleep(delay)

    return sorted(discovered)[:max_articles], failed


def fetch_articles(urls: Iterable[str], output_dir: Path, delay: float, refresh: bool, robots) -> tuple[list[dict], list[dict]]:
    raw_dir = output_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    articles: list[dict] = []
    failed: list[dict] = []

    existing_by_url = {item.get("url"): item for item in read_json(output_dir / "articles.json", [])}

    for url in urls:
        raw_path = raw_dir / safe_name(url)
        if not refresh and raw_path.exists():
            html_text = raw_path.read_text(encoding="utf-8", errors="replace")
            fetched_at = existing_by_url.get(url, {}).get("fetched_at", "")
            status = "cached"
        else:
            if not can_fetch(robots, url):
                failed.append({"url": url, "stage": "fetch", "error": "blocked_by_robots"})
                continue
            status_code, html_text, err = fetch_url(url)
            if err or status_code >= 400 or not html_text:
                failed.append({"url": url, "stage": "fetch", "status": status_code, "error": err})
                continue
            raw_path.write_text(html_text, encoding="utf-8")
            fetched_at = now_iso()
            status = "fetched"
            time.sleep(delay)

        body = body_text_from_html(html_text)
        canonical = canonical_from_html(html_text, url)
        record = {
            "url": url,
            "canonical_url": canonical,
            "title": title_from_html(html_text),
            "date": date_from_html(html_text),
            "body_text": body,
            "body_excerpt": excerpt(body),
            "fetched_at": fetched_at or now_iso(),
            "source_html_path": str(raw_path),
            "article_id": article_id(url),
            "category": "",
            "tags": [],
            "fetch_status": status,
            "fetch_error": "",
            "content_hash": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        }
        articles.append(record)

    return articles, failed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-articles", type=int, default=50)
    parser.add_argument("--delay-seconds", type=float, default=2.0)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--output-dir", default="data/ameblo")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    robots = load_robots()

    discovered, discover_failed = discover_article_urls(args.max_articles, args.delay_seconds, output_dir, args.refresh, robots)
    articles, fetch_failed = fetch_articles(discovered, output_dir, args.delay_seconds, args.refresh, robots)

    failed = discover_failed + fetch_failed
    write_json(output_dir / "articles.json", articles)
    write_csv(output_dir / "articles.csv", articles)
    write_json(output_dir / "failed_urls.json", failed)
    write_json(output_dir / "fetch_log.json", {
        "generated_at": now_iso(),
        "blog_top": BLOG_TOP,
        "user_agent": USER_AGENT,
        "max_articles": args.max_articles,
        "delay_seconds": args.delay_seconds,
        "discovered_count": len(discovered),
        "fetched_count": len(articles),
        "failed_count": len(failed),
        "failed_urls_path": str(output_dir / "failed_urls.json"),
    })

    print(f"Discovered: {len(discovered)}")
    print(f"Fetched/indexable: {len(articles)}")
    print(f"Failed/skipped: {len(failed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
