---
id: adr-2607010930-kawaraban-g4-internal-fulltext-buffer
title: "kawaraban G4 internal fulltext buffer — PRIVATE analysis cache for the yomi intel consumer (実装, NOT a G4 / Charter-Rider weakening)"
status: accepted
doc_type: adr
topic: kawaraban-g4-internal-fulltext-buffer
authoritative: true
last_verified: 2026-07-01
priority: 4.0
axis: architecture
weight: 0.40
priority_note: "Owner directive 2026-07-01 ('kawaraban G4 internal buffer'): kawaraban may hold a fetched article BODY in a PRIVATE internal buffer so the yomi news-intel actor (ADR-2607010900) can read full text for analysis. The PUBLIC G4 invariant is unchanged and absolute — :news.article/full-text stays :db/allowed [false] / lexicon :const false; article_mirror's fullText stays false in the public projection; the body is never transacted to the public Datom log / never projected to a 面 / never published. This is an 実装 (engineering) addition at the implementation layer, NOT a Tier-1 Charter-Rider weakening: the public-facing copyright membrane is identical; only an internal, non-public, analysis-only cache is added. ZERO charter invariant amendments."
authoritative_for:
  - "the fulltext_cache cell (cells/fulltext_cache/) — a PRIVATE buffer that caches a fetched article body for an analysis consumer, off the public Datom log"
  - "the G4 public/private split: PUBLIC (:news.article/full-text :db/allowed [false], article_mirror refuses full_text=true) is absolute; PRIVATE (data/ingest/fulltext-buffer/, gitignored) may hold the body for analysis only"
  - "the access membrane carried verbatim from article_mirror (outlet :access ∈ {:open :registration-wall} only; paywall/terminal bodies uncacheable)"
depends_on:
  - adr-2606061900   # kawaraban G4 (the public invariant this stays within)
  - adr-2607010900   # yomi (the analysis consumer that reads the buffer)
related:
  - "com-etzhayyim-kawaraban/cells/fulltext_cache/state_machine.cljc"
supersedes: []
superseded_by: []
---

# ADR-2607010930: kawaraban G4 internal fulltext buffer

**Status**: accepted (実装-layer, not charter) · **Date**: 2026-07-01 · **Deciders**: Jun Kawasaki

## Context

kawaraban's G4 (copyright / link-out) makes `:news.article/full-text`
`:db/allowed [false]` and the `article_mirror` cell REFUSE `full_text=true` — a mirrored
article projects headline + link + ≤280-char excerpt ONLY. This is the public copyright
membrane and it is load-bearing.

The yomi news-intelligence actor (ADR-2607010900) needs the article BODY to ground an intel
assessment. Two options were considered:

1. **Weaken G4 in place** (allow `:news.article/full-text` in the public ontology) — rejected:
   that is the Tier-1 Charter-Rider copyright membrane the README's "charter-clean inverse
   of a news app" table exists to protect; it would re-publish NHK/Reuters/AP/AFP full text
   on a public medium.
2. **Hold full text PRIVATELY, off the public log** — accepted. yomi grounds its analysis on
   a body kawaraban caches in an internal buffer that is never projected publicly.

## Decision

Add a `fulltext_cache` cell (`cells/fulltext_cache/`) that caches a fetched article BODY in
`data/ingest/fulltext-buffer/` (gitignored), keyed by article_id with url/outlet/fetched-at
provenance. **The PUBLIC G4 invariant is unchanged and absolute**: `article_mirror`'s
`fullText` stays `false` in the public projection regardless of what is cached; the body is
never transacted to the public Datom log, never projected to a 面, never published.

This is an **実装 (engineering) addition at the implementation layer**, not a Tier-1
Charter-Rider weakening — per the substrate-boundary tier discipline, "where data is stored
internally" is 実装, changeable without a charter amendment. The public-facing copyright
membrane (never publish / never represent full text in the public ontology) is identical
before and after.

The access membrane is carried verbatim from `article_mirror`: a body is cached only for
`:outlet/access ∈ {:open :registration-wall}` — a paywall / proprietary-terminal body is
REFUSED (kawaraban cannot have fetched it on the public-web-up contract). `.solve()` raises
at R0 (live public-web fetch is G8-gated = Council Lv6+ + operator).

## Status

🟡 R0 scaffold (cell + tests, bb-verified: open→cached(private, publicFullText=false),
paywall→refused, missing-provenance→refused). PR: etzhayyim/com-etzhayyim-kawaraban#2.
