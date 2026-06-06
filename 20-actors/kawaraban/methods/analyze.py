#!/usr/bin/env python3
"""kawaraban 瓦版 — compose an EDITION (front-面 digest) from the news-medium graph.

ADR-2606060900. The composer ranks articles into 面 (sections) using G2 PUBLIC-GOOD
signals ONLY — recency, section-fit, source-diversity, actor-relevance — and NEVER by
paid placement, sponsorship, engagement, or dwell-time (those signals are not even
representable; `assert_rank_signals` RAISES if an illegal signal is requested).

It emits:
  1. out/edition.md                 — a human-readable front-面 edition: 一面 leads + each
                                      populated 面, every article shown as
                                      headline + outlet/source + link (mirror) or
                                      source-actor (actor-event) + the actors it wires.
  2. out/news-medium.kotoba.edn     — derived :news.issue/* + :news.medium.link/* datoms
                                      (the actor-to-actor connection edges), flagged
                                      :derived (never re-ingested as authoritative).

Every article is an OBSERVATION carried by a medium — never a verdict (G1), never spoken in
anyone's name (G9). The edition is dated, not final (:news.issue/final unrepresentable, G10),
unsigned + unpublished at R0 (G7/G8 — live publish is Council Lv6+ + operator).

stdlib only. Usage:
    python3 analyze.py [seed.edn] [--out OUTDIR]
"""
from __future__ import annotations
import sys
import pathlib

from route import (  # same-dir import (tests/CLI run from methods/)
    load_edn, classify, validate, wire_table, section_men,
    actor_targets, actor_links, _short,
)

# G2 INVARIANT — the only ranking signals that exist. Engagement / paid placement /
# sponsorship / dwell-time are NOT members and can never be added.
ALLOWED_RANK_SIGNALS = ("recency", "section-fit", "source-diversity", "actor-relevance", "geo-proximity")
USED_SIGNALS = ("recency", "source-diversity", "actor-relevance")

# 面 display order (mirrors a real newspaper's section order).
MEN_ORDER = ["front", "politics", "economy", "international", "society",
             "culture", "science", "sports", "local", "opinion"]


def assert_rank_signals(signals) -> None:
    """G2 — refuse any ranking signal outside the public-good allowlist."""
    for s in signals:
        if s not in ALLOWED_RANK_SIGNALS:
            raise ValueError(
                f"G2: ranking signal {s!r} is not public-good ({ALLOWED_RANK_SIGNALS}); "
                "paid-placement / engagement / dwell-time are unrepresentable (Charter §1.13 + Rider §2)"
            )


def _men_of(article, sections) -> str:
    sid = article.get(":news.article/section")
    return section_men(sid, sections) if sid else "front"


def score(article, mentions, newest, oldest, seen_outlets) -> float:
    """Blended G2 public-good score. Higher = more prominent. Deterministic."""
    # recency: linear in [0,1] over the dataset span (newest=1).
    as_of = article.get(":news.article/as-of", 0)
    span = max(1, newest - oldest)
    recency = (as_of - oldest) / span
    # actor-relevance: how many first-party actors this article wires together.
    relevance = len(set(actor_targets(article.get(":news.article/id"), mentions)))
    # source-diversity: a fresh outlet/source is promoted over a repeat.
    src = article.get(":news.article/outlet") or article.get(":news.article/source-actor") or "?"
    diversity = 0.0 if src in seen_outlets else 1.0
    return round(0.5 * recency + 0.3 * min(relevance, 3) / 3.0 + 0.2 * diversity, 6)


def compose(rows, lead_n: int = 4):
    outlets, sections, articles, mentions, wires = classify(rows)
    validate(articles)              # gates first — refuse before composing
    assert_rank_signals(USED_SIGNALS)
    table = wire_table(wires)
    edges, degree = actor_links(articles, mentions)

    as_ofs = [a.get(":news.article/as-of", 0) for a in articles] or [0]
    newest, oldest = max(as_ofs), min(as_ofs)

    # rank for the 一面 leads with a source-diversity pass (promote outlet variety).
    ranked, seen = [], set()
    for a in sorted(articles, key=lambda x: -x.get(":news.article/as-of", 0)):
        ranked.append((score(a, mentions, newest, oldest, seen), a))
        seen.add(a.get(":news.article/outlet") or a.get(":news.article/source-actor"))
    ranked.sort(key=lambda sa: (-sa[0], -sa[1].get(":news.article/as-of", 0)))
    leads = [a for _, a in ranked[:lead_n]]

    # group by 面
    by_men: dict[str, list] = {m: [] for m in MEN_ORDER}
    for a in sorted(articles, key=lambda x: -x.get(":news.article/as-of", 0)):
        by_men.setdefault(_men_of(a, sections), []).append(a)

    return {
        "outlets": outlets, "sections": sections, "articles": articles,
        "mentions": mentions, "wires": wires, "table": table,
        "edges": edges, "degree": degree, "leads": leads, "by_men": by_men,
        "newest": newest,
    }


def _article_line(a, sections, mentions) -> str:
    head = a.get(":news.article/headline", "")
    wired = [_short(x) for x in sorted(set(actor_targets(a.get(":news.article/id"), mentions)))]
    wired_s = (" — wires: " + ", ".join(wired)) if wired else ""
    if a.get(":news.article/kind") == ":mirror":
        outlet = a.get(":news.article/outlet", "?").split(".", 1)[-1]
        url = a.get(":news.article/url", "")
        return f"- **{head}** — _{outlet}_ ([link]({url})){wired_s}"
    actor = _short(a.get(":news.article/source-actor", "?"))
    return f"- **{head}** — _actor-event: {actor}_{wired_s}"


def render_md(c) -> str:
    sections, mentions = c["sections"], c["mentions"]
    L = ["# 瓦版 kawaraban — Edition (as-of snapshot)", ""]
    L.append("_A news MEDIUM: real-media mirror + actor-to-actor wire. Link-out, no full "
             "text (G4); no verdict (G1); no ads / no engagement ranking (G2); no reader "
             "profile (G3); not final (G10). Unsigned + unpublished at R0 (G7/G8)._")
    L.append("")
    L.append(f"Ranked by public-good signals only: {', '.join(USED_SIGNALS)}.")
    L.append("")
    # 一面 leads
    L.append("## 一面 — Front Page")
    for a in c["leads"]:
        L.append(_article_line(a, sections, mentions))
    L.append("")
    # per-面
    for men in MEN_ORDER:
        if men == "front":
            continue
        arts = c["by_men"].get(men, [])
        if not arts:
            continue
        name = next((sections[s].get(":news.section/name-ja", men)
                     for s in sections if section_men(s, sections) == men), men)
        L.append(f"## {name} ({men})")
        for a in arts:
            L.append(_article_line(a, sections, mentions))
        L.append("")
    # the actor-to-actor wire
    L.append("## Actor-to-actor wire (the medium)")
    L.append("Co-mention edges — kawaraban connects these actors by carrying the same story:")
    for pair, n in sorted(c["edges"].items(), key=lambda kv: (-kv[1], sorted(kv[0]))):
        a, b = sorted(_short(x) for x in pair)
        L.append(f"- `{a}` —{n}— `{b}`")
    L.append("")
    L.append("Most-wired actors: " + ", ".join(
        f"{_short(act)} ({d})" for act, d in
        sorted(c["degree"].items(), key=lambda kv: (-kv[1], kv[0]))[:5]))
    L.append("")
    return "\n".join(L)


def render_edn(c) -> str:
    issue_id = f"issue.kawaraban.{c['newest']}"
    L = [";; kawaraban derived edition + actor-to-actor link edges (ADR-2606060900)",
         ";; :derived — NOT re-ingested as authoritative. published=false / final=false (G7/G8/G10).",
         "["]
    sec_ids = [s for s in c["sections"]]
    lead_ids = [a.get(":news.article/id") for a in c["leads"]]
    L.append(f' {{:news.issue/id "{issue_id}" :news.issue/as-of {c["newest"]} '
             f':news.issue/sections {len(sec_ids)} :news.issue/lead-count {len(lead_ids)} '
             f':news.issue/published false :news.issue/server-held-key false :news.issue/final false '
             f':news.issue/derived true}}')
    for pair, n in sorted(c["edges"].items(), key=lambda kv: (-kv[1], sorted(kv[0]))):
        a, b = sorted(pair)
        lid = f'link.{_short(a)}--{_short(b)}'
        L.append(f' {{:news.medium.link/id "{lid}" :news.medium.link/a "{a}" '
                 f':news.medium.link/b "{b}" :news.medium.link/shared {n} :news.medium.link/derived true}}')
    L.append("]")
    return "\n".join(L)


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    out_dir = pathlib.Path(__file__).resolve().parent / "out"
    if "--out" in argv:
        out_dir = pathlib.Path(argv[argv.index("--out") + 1])
    seed = pathlib.Path(args[0]) if args else (
        pathlib.Path(__file__).resolve().parent.parent / "data" / "seed-news-graph.kotoba.edn")
    rows = load_edn(seed)
    c = compose(rows)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "edition.md").write_text(render_md(c), encoding="utf-8")
    (out_dir / "news-medium.kotoba.edn").write_text(render_edn(c), encoding="utf-8")
    print(f"composed edition: {len(c['articles'])} articles across "
          f"{sum(1 for m in MEN_ORDER if c['by_men'].get(m))} 面; "
          f"{len(c['edges'])} actor-to-actor edges; {len(c['leads'])} 一面 leads")
    print(f"→ {out_dir/'edition.md'}\n→ {out_dir/'news-medium.kotoba.edn'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
