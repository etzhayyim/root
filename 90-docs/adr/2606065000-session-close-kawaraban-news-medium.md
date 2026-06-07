---
id: adr-2606065000-session-close-kawaraban-news-medium
title: "ADR-2606065000: Session close — kawaraban 瓦版 news medium (real-media mirror + actor-to-actor wire) landed, merged, registries updated"
status: active
doc_type: adr
topic: kawaraban-news-medium-actor
authoritative: false
last_verified: 2026-06-06
priority: 5.0
axis: actor
weight: 0.5
depends_on:
  - adr-2606061900-kawaraban-news-medium-actor-r0
  - adr-2605263600-kataribe-press-publishing-translation-r0
  - adr-2605231902-feed-post-membrane-and-feed-discover-projection
related:
  - 90-docs/adr/2606063000-session-close-ooyake-world-model-reconcile-loop.md
supersedes: []
superseded_by: []
---

# Context

Question that opened the session: *「https://etzhayyim.com/apps の news actor を kotoba wasm
ベースで設計, また murakumo fleet で動くように。また news actor は 実際の news media の 面に
合わせて, actor と actor をつなげる, medium として news actor を設計」.*

Answer at the time: there was **no news actor**. The closest, **kataribe 語部**
(ADR-2605263600), is etzhayyim's OWN press — a *primary voice*, not a medium. Nothing (a)
mirrored the world's real news media into kotoba, or (b) acted as the connective **medium**
wiring the first-party actors together. The naive "news app" shape is unconstitutional
(ad-funded Charter-Rider §2 / engagement-optimized Charter §1.13 / reader-surveilling /
truth-adjudicating ake/danjo boundary / content-republishing), so the design had to be its
charter-clean inverse.

# Decision

Built **kawaraban 瓦版** (ADR-2606061900 — the canonical design home), a Tier-B news-medium
actor: a public-square **mirror** of real news media's 面 (sections) + the connective
**medium** that projects each first-party actor's Datom as-of events into the matching 面 and
wires actors together via `:news.mention` edges (the article × mention × 面 graph IS the
wire). kotoba-wasm-native, Murakumo fleet, 11 structural gates, ZERO invariant amendments.
This ADR records the session close and the registry reconciliation.

# Consequences

**Landed + merged to `main` (PR #1172, all CI green):**

- **Actor** `20-actors/kawaraban/` — manifest, 6 lexicons (`com.etzhayyim.kawaraban.*` + the
  canonical `00-contracts/lexicons/com/etzhayyim/kawaraban/*.json`), 5 coded cells
  (`.solve()` raises at R0), `route.py` (the medium: actor→面 wire + co-mention graph),
  `analyze.py` (edition composer — G2 public-good ranking only), `ingest.py` (offline
  outlet membrane), `wasm/wit/world.wit` (kotoba-wasm component), Murakumo fleet placement,
  `:representative` seed (7 outlets / 10 面 / 9 wires / 12 articles / 24 mentions).
- **Ontology** `00-contracts/schemas/news-medium-ontology.kotoba.edn` (11 gates encoded
  structurally: each in schema `:db/allowed`/enum + lexicon `const`/enum + Python
  `ValueError`).
- **Registered** in `INFRA_ACTORS` → `did:web:etzhayyim.com:actor:kawaraban` (surfaces on
  `/apps`, `/actors`, `/search`).
- **46 tests green** (route 11 + analyze 7 + ingest 8 + cells 20; `./run_tests.sh`).
- **CI fixes during merge**: generated the canonical JSON lexicons (manifest↔lexicon drift
  audit) and regenerated `90-docs/_registry/{docs.json,graph.jsonld}` (the `.md → docs.json
  → graph.jsonld` freshness chain); all of `monorepo-health`, `docs-registry-freshness`,
  `docs-graph-jsonld-freshness`, `lint-and-test`, and CodeQL `Analyze` pass.

**Registry reconciliation (this closing change):**

- `deps.toml` — added the `[[adrs]]` entry for ADR-2606061900 (333 ADRs total).
- `90-docs/adr/README.md` — added the Active-table rows for ADR-2606061900 (kawaraban) and
  this session-close ADR.
- `90-docs/_registry/{docs.json,graph.jsonld}` — regenerated to include both new docs.

**Boundaries preserved**: kawaraban is NOT kataribe (kataribe is the primary voice; kawaraban
is the medium, authoring no `:original` claim — G11). It never adjudicates (ake/danjo own
that — G1), never advertises (G2), never profiles a reader (G3), never republishes full text
(G4), never speaks AS anyone (G9).

**Honest state**: R0 = design + datafication + offline composition only. No live RSS/outlet
ingest, no live publish — all G8-gated (Council Lv6+ + operator). The `:representative` seed
uses neutral illustrative headlines, not captured real articles. R1 (live-but-gated
public-facing-page ingest + actor-event projection to the feed-post membrane, ADR-2605231902)
is the next step, behind the Council gate.

# Alternatives Considered

- **Extend kataribe** instead of a new actor — rejected: kataribe is a primary voice
  (authors original copy); the requirement was explicitly a *medium* that mirrors and
  connects, which is the opposite stance (G11). Keeping them distinct preserves a clean
  sibling boundary.
- **A conventional news feed with light guardrails** — rejected: ads, engagement ranking,
  reader profiling, and truth-verdicts must be *unrepresentable*, not merely discouraged;
  the inverse-by-construction design (gates in three places each) is the only charter-safe
  form.

# References

- ADR-2606061900 (kawaraban news medium — canonical design home)
- ADR-2605263600 (kataribe — etzhayyim's own press; the sibling boundary)
- ADR-2605231902 (feed-post membrane — the R1 projection substrate)
- ADR-2606042330 (entity-as-actor mirror invariant)
- ADR-2605231525 (no-server-key) · ADR-2605312345 (kotoba canonical state)
