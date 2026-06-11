#!/usr/bin/env python3
"""Fetch a web page, convert it to JSON-LD, and optionally classify with LASER."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Any
from urllib import request
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse


DEFAULT_LABELS: list[tuple[str, str]] = [
    ("business", "Business strategy, management, company operations, enterprise topics."),
    ("finance", "Finance, accounting, investment, markets, taxation, financial regulations."),
    ("real-estate", "Real estate, property, land ownership, housing, rental, urban development."),
    ("technology", "Software, AI, data, cloud infrastructure, developer tooling, IT systems."),
    ("government", "Government policy, public administration, regulation, legal frameworks."),
    ("healthcare", "Healthcare, medicine, hospitals, public health, patient services."),
    ("education", "Education, schools, universities, training, learning outcomes."),
    ("logistics", "Supply chain, transportation, warehousing, procurement, delivery operations."),
    ("security", "Cybersecurity, risk management, compliance, threat intelligence, safety."),
    ("marketing", "Marketing, branding, growth, customer acquisition, campaign execution."),
    ("media", "News, publishing, content production, broadcasting, creator economy."),
    ("research", "Research findings, analysis reports, methodologies, evidence-based insights."),
]


def _norm_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


class PageTextParser(HTMLParser):
    """Minimal HTML text extractor for title/meta/headings/body."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip = False
        self._current_tag: str | None = None
        self._buf: list[str] = []
        self.title_parts: list[str] = []
        self.headings: list[str] = []
        self.paragraphs: list[str] = []
        self.meta: dict[str, str] = {}
        self.lang: str = ""
        self._collect_tags = {"title", "h1", "h2", "h3", "p"}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        t = tag.lower()
        if t in {"script", "style", "noscript"}:
            self._skip = True
            return

        attr_map = {k.lower(): (v or "") for k, v in attrs}
        if t == "html":
            lang = attr_map.get("lang", "")
            if lang and not self.lang:
                self.lang = lang.split("-")[0].lower()
        if t == "meta":
            key = (
                attr_map.get("property")
                or attr_map.get("name")
                or attr_map.get("itemprop")
                or attr_map.get("http-equiv")
            )
            val = attr_map.get("content", "")
            if key and val:
                self.meta[key.lower()] = _norm_text(val)
        if t in self._collect_tags:
            self._current_tag = t
            self._buf = []

    def handle_endtag(self, tag: str) -> None:
        t = tag.lower()
        if t in {"script", "style", "noscript"}:
            self._skip = False
            return
        if self._current_tag == t:
            text = _norm_text("".join(self._buf))
            if text:
                if t == "title":
                    self.title_parts.append(text)
                elif t in {"h1", "h2", "h3"}:
                    self.headings.append(text)
                elif t == "p":
                    self.paragraphs.append(text)
            self._current_tag = None
            self._buf = []

    def handle_data(self, data: str) -> None:
        if self._skip or not self._current_tag:
            return
        self._buf.append(data)


@dataclass
class PageInfo:
    url: str
    final_url: str
    headline: str
    description: str
    body: str
    language: str
    published: str
    author: str


def fetch_html(url: str, timeout_sec: int = 20) -> tuple[str, str]:
    req = request.Request(
        url,
        headers={
            "User-Agent": "etzhayyim-jsonld-builder/1.0",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with request.urlopen(req, timeout=timeout_sec) as resp:
        raw = resp.read()
        final_url = resp.geturl()
        content_type = resp.headers.get("Content-Type", "")
    m = re.search(r"charset=([A-Za-z0-9._-]+)", content_type)
    enc = m.group(1) if m else "utf-8"
    try:
        html = raw.decode(enc, errors="replace")
    except LookupError:
        html = raw.decode("utf-8", errors="replace")
    return html, final_url


def parse_page(url: str, html: str, final_url: str) -> PageInfo:
    p = PageTextParser()
    p.feed(html)

    headline = (
        p.meta.get("og:title")
        or p.meta.get("twitter:title")
        or (p.headings[0] if p.headings else "")
        or (p.title_parts[0] if p.title_parts else "")
    )
    description = (
        p.meta.get("description")
        or p.meta.get("og:description")
        or p.meta.get("twitter:description")
        or ""
    )
    paragraphs = [_norm_text(x) for x in p.paragraphs if _norm_text(x)]
    body = "\n\n".join(paragraphs[:80])
    if not body:
        body = "\n\n".join([_norm_text(x) for x in p.headings[:20]])
    language = p.lang or "und"
    published = (
        p.meta.get("article:published_time")
        or p.meta.get("date")
        or p.meta.get("pubdate")
        or ""
    )
    author = (
        p.meta.get("author")
        or p.meta.get("article:author")
        or p.meta.get("og:article:author")
        or ""
    )

    return PageInfo(
        url=url,
        final_url=final_url,
        headline=_norm_text(headline),
        description=_norm_text(description),
        body=_norm_text(body),
        language=language,
        published=_norm_text(published),
        author=_norm_text(author),
    )


def load_labels(args: argparse.Namespace) -> list[tuple[str, str]]:
    labels: list[tuple[str, str]] = []
    if args.labels_file:
        with open(args.labels_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            labels.extend([(str(k), str(v)) for k, v in data.items()])
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and "name" in item:
                    labels.append((str(item["name"]), str(item.get("description", item["name"]))))
                elif isinstance(item, str):
                    labels.append((item, item))
    if args.label:
        for raw in args.label:
            if "::" in raw:
                name, desc = raw.split("::", 1)
                labels.append((_norm_text(name), _norm_text(desc)))
            else:
                t = _norm_text(raw)
                labels.append((t, t))
    if not labels:
        labels = DEFAULT_LABELS[:]
    return [(n, d) for n, d in labels if n and d]


def call_laser_embed(laser_url: str, texts: list[str], lang: str) -> list[list[float]]:
    endpoint = laser_url.rstrip("/") + "/embed"
    payload = {"texts": texts, "lang": lang or "en", "normalize": True}
    req = request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=30) as resp:
        body = json.loads(resp.read().decode("utf-8", errors="replace"))
    vectors = body.get("vectors", [])
    if not isinstance(vectors, list):
        raise ValueError("Invalid LASER response: vectors missing")
    return vectors


def cosine(a: list[float], b: list[float]) -> float:
    dot = 0.0
    na = 0.0
    nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (math.sqrt(na) * math.sqrt(nb))


def classify_with_laser(
    laser_url: str, page_text: str, labels: list[tuple[str, str]], lang: str, top_k: int
) -> list[dict[str, Any]]:
    texts = [page_text] + [desc for _, desc in labels]
    vectors = call_laser_embed(laser_url, texts, lang=lang)
    if len(vectors) != len(texts):
        raise ValueError("Unexpected LASER vector length")
    doc_vec = vectors[0]
    scores = []
    for i, (name, _desc) in enumerate(labels, start=1):
        score = cosine(doc_vec, vectors[i])
        scores.append({"label": name, "score": round(float(score), 6)})
    scores.sort(key=lambda x: x["score"], reverse=True)
    return scores[: max(1, top_k)]


def build_jsonld(
    page: PageInfo,
    doc_type: str,
    classification: list[dict[str, Any]],
    include_scores: bool,
) -> dict[str, Any]:
    host = urlparse(page.final_url).netloc
    data: dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": doc_type,
        "url": page.final_url,
        "headline": page.headline or host,
        "description": page.description or (page.body[:240] if page.body else ""),
        "articleBody": page.body,
        "inLanguage": page.language or "und",
        "publisher": {"@type": "Organization", "name": host},
    }
    if page.author:
        data["author"] = {"@type": "Person", "name": page.author}
    if page.published:
        data["datePublished"] = page.published
    if classification:
        data["about"] = [{"@type": "Thing", "name": x["label"]} for x in classification]
        data["keywords"] = [x["label"] for x in classification]
        if include_scores:
            data["etzhayyim:classification"] = classification
    return data


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Convert a URL document to JSON-LD with LASER classification.")
    ap.add_argument("url", help="Target page URL")
    ap.add_argument("--type", default="Article", help="Schema.org type (default: Article)")
    ap.add_argument(
        "--laser-url",
        default="http://laser.ml-inference.svc.cluster.local:8080",
        help="LASER service base URL",
    )
    ap.add_argument("--no-classify", action="store_true", help="Disable LASER classification")
    ap.add_argument("--labels-file", help="JSON file for labels (dict or list)")
    ap.add_argument(
        "--label",
        action="append",
        help="Label string or name::description (repeatable)",
    )
    ap.add_argument("--top-k", type=int, default=3, help="Top K labels in output (default: 3)")
    ap.add_argument("--output", help="Output JSON-LD file path (default: stdout)")
    ap.add_argument("--include-scores", action="store_true", help="Include classification scores in JSON-LD")
    return ap.parse_args()


def main() -> int:
    args = parse_args()

    try:
        html, final_url = fetch_html(args.url)
        page = parse_page(args.url, html, final_url)

        classification: list[dict[str, Any]] = []
        if not args.no_classify:
            labels = load_labels(args)
            basis = _norm_text("\n\n".join([page.headline, page.description, page.body]))[:12000]
            if basis:
                classification = classify_with_laser(
                    laser_url=args.laser_url,
                    page_text=basis,
                    labels=labels,
                    lang=page.language if page.language != "und" else "en",
                    top_k=args.top_k,
                )

        payload = build_jsonld(
            page=page,
            doc_type=args.type,
            classification=classification,
            include_scores=args.include_scores,
        )
        out = json.dumps(payload, ensure_ascii=False, indent=2)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(out + "\n")
        else:
            print(out)
        return 0
    except HTTPError as e:
        print(f"HTTP error: {e.code} {e.reason}", file=sys.stderr)
    except URLError as e:
        print(f"URL error: {e.reason}", file=sys.stderr)
    except Exception as e:  # pragma: no cover
        print(f"Error: {e}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
