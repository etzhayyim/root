---
id: adr-2606061900-kawaraban-news-medium-actor-r0
title: "kawaraban 瓦版 — news medium (Tier-B actor R0; real-media mirror + actor-to-actor wire; the charter-clean inverse of a news app)"
status: proposed-pending-council-ratification
doc_type: adr
topic: kawaraban-news-medium-actor
authoritative: true
last_verified: 2026-06-06
priority: 6.2
axis: actor
weight: 0.62
priority_note: "Answers 「https://etzhayyim.com/apps の news actor を kotoba wasm ベースで設計, また murakumo fleet で動くように。また news actor は 実際の news media の 面に合わせて, actor と actor をつなげる, medium として news actor を設計」. There was no news actor (kataribe is etzhayyim's OWN press, a primary voice; no actor mirrored the world's news media or wired the first-party actors together as a medium). A naive news app is ad-funded / engagement-optimized / reader-surveilling / truth-adjudicating / content-republishing — ALL prohibited (Charter §1.13 + Charter-Rider §2 + ake/danjo non-adjudication + copyright). kawaraban is its INVERSE (okaimono/mitooshi/kamado pattern): a public-square MIRROR + connective MEDIUM that links out, never advertises, never profiles a reader, never republishes full text, never adjudicates, never speaks AS anyone. The 面 (sections) mirror real news-media sectioning; the article × mention × 面 graph is the actor-to-actor wire. ZERO invariant amendments."
authoritative_for:
  - "kawaraban actor scope (real-media mirror into kotoba + first-party actor Datom-event projection into the matching 面 as the actor-to-actor medium; design-only)"
  - "the mirror-not-adjudicator invariant (:news.article/verdict + :truth-rating :db/allowed [false]; ake/danjo own truth)"
  - "the no-ads / no-engagement-rank invariant (:news.rank/signal excludes paid-placement/sponsored/engagement/dwell-time)"
  - "the no-reader-surveillance invariant (no :reader entity; :article/personalized-for :db/allowed [false])"
  - "the copyright / link-out invariant (:article/full-text :db/allowed [false]; headline + link + bounded fair-use excerpt only)"
  - "the connective-by-construction medium gate (every article is :mirror or :actor-event; :original unrepresentable)"
depends_on:
  - adr-2605263600-kataribe-press-publishing-translation-r0
  - adr-2605231902-feed-post-membrane-and-feed-discover-projection
  - adr-2606042330-entity-as-actor-society-scale-social-mirror
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605231525-server-side-signing-capability-boundary
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2606014600-wasm-actor-runtime-round-2
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
related:
  - adr-2606041827-watari-live-ship-aircraft-position-kg-r0
  - adr-2606012600-watatsuna-submarine-cable-resilience
  - adr-2606051800-mitooshi-probabilistic-forecasting-observatory-r0
  - adr-2605302300-kanae-government-fiscal-flow-visualization-r0
  - adr-2605301600-danjo-public-accountability-oversight-r0
  - adr-2606052100-ake-community-edit-membrane-r0
supersedes: []
superseded_by: []
---

# ADR-2606061900: kawaraban 瓦版 — news medium (R0)

**Status**: proposed-pending-council-ratification
**Date**: 2026-06-06
**Deciders**: Jun Kawasaki (Founder, Seat 1) — pending Council ratification

# Context

The question: *「https://etzhayyim.com/apps の news actor を kotoba wasm ベースで設計,
また murakumo fleet で動くように。また news actor は 実際の news media の 面に合わせて,
actor と actor をつなげる, medium として news actor を設計」.*

**The honest pre-state.** There is no news actor. The closest is **kataribe 語部**
(ADR-2605263600) — but kataribe is etzhayyim's OWN press: a *primary voice* that authors
original copy, translates, and publishes. Nothing in the roster (a) mirrors the world's
real news media into kotoba, or (b) acts as the connective **medium** that wires the
first-party actors to one another. The `/apps` surface lists actors but has no news face.

**Why the naive shape is unconstitutional.** A "news app" in its素直 form is:
ad-funded (Charter-Rider §2 bars third-party ads/affiliate), engagement-optimized /
addictive (Charter §1.13 bars dark-pattern engagement design), reader-surveilling
(per-reader profiling for a personalized feed), an adjudicator of truth (a fact-check
"true/false" verdict — which is **ake**'s community-edit and **danjo**'s discrepancy
boundary, never a news desk's), and a republisher of copyrighted article bodies. Every one
of those is a constitutional prohibition. The reason a news app was never built is that the
obvious form is unconstitutional, not that it was overlooked.

So, as with okaimono inverting Amazon, yadori inverting GoDaddy, mitooshi inverting a quant
bot, and kamado making a fossil-feedstock refinery unrepresentable, the design problem is
to build the **charter-clean inverse** of a news app — a public-square **mirror** + a
connective **medium**.

**The two requirements in the question map cleanly onto kotoba primitives:**

- *「実際の news media の 面に合わせて」* — a real newspaper's surface is its **面**
  (一面 / 政治 / 経済 / 国際 / 社会 / 文化 / 科学 / スポーツ). kawaraban's ontology models
  exactly those sections; a mirrored article is filed into the same 面 a real outlet would
  use. The actor's surface looks like a newspaper because it mirrors a newspaper's surface.
- *「actor と actor をつなげる, medium として」* — the medium is the connective tissue. Each
  first-party actor's own Datom **as-of** events project into the matching 面 (reusing the
  feed-post membrane, ADR-2605231902) as `:article/kind :actor-event`, and every article
  carries `:news.mention` edges to the actors/entities it concerns. The
  **article × mention × 面 graph IS the actor-to-actor wire**: danjo finds a discrepancy →
  kawaraban carries it into 政治 → kanae renders the fiscal view; a chokepoint story files
  into 国際 and its mention edges link watari + watatsuna + mitooshi into one cluster.

# Decision

Introduce **kawaraban 瓦版**, a Tier-B **news-medium** actor, **kotoba-wasm-native** and
deployed on the **Murakumo fleet**. 瓦版 was the original Japanese news medium — Edo-period
clay-block broadsheets cried and sold in the street: a *sheet* (面), not an oracle. It
carries *what was said* and *who it concerns*; it does not rule what is true.

kawaraban has **two faces over one kotoba Datom log**:

1. **Mirror** (`:article/kind :mirror`) — datafy a real outlet's PUBLIC facing page into the
   Datom log as an append-only as-of trail: `headline + canonical :url + bounded fair-use
   :excerpt + :outlet + :as-of`. It links out; it never stores the body (G4) and never
   rules truth (G1). Only public/open facing pages are mirrored — paywalled / proprietary
   terminal feeds are unrepresentable (G4; kanjo §2(c) anti-gatekeeping precedent: read the
   public page, link to it; the proprietary *compilation* does not flow).

2. **Medium** (`:article/kind :actor-event`) — project a first-party actor's Datom as-of
   event into the matching 面, member-signed (G7), as the connective wire between actors.

## The 11 structural gates (each enforced in THREE places)

Following the nusa/tazuna/kamado/mitooshi/ake pattern, each invariant lives in the schema
(`:db/allowed`/enum) **and** the lexicon (`const`/`enum`) **and** the Python
(`ValueError`/refusal) — so a charter violation is not merely discouraged, it is
**unrepresentable**.

- **G1 mirror-not-adjudicator** — `:news.article/verdict` + `:truth-rating` are
  `:db/allowed [false]`. kawaraban records that outlet X published headline H at T; it
  cannot express that H is true/false (ake/danjo boundary).
- **G2 no-ads / no-engagement-rank** — `:news.rank/signal` enum is
  `{:recency :section-fit :source-diversity :actor-relevance :geo-proximity}`;
  `:paid-placement` / `:sponsored` / `:engagement` / `:dwell-time` are not members
  (Charter §1.13 + Charter-Rider §2).
- **G3 no-reader-surveillance** — there is no `:reader` entity; `:article/personalized-for`
  is `:db/allowed [false]`. The 面 is identical for everyone (the public square; watari's
  person-exclusion invariant applied to the reader).
- **G4 copyright / link-out** — `:article/full-text` is `:db/allowed [false]`; headline +
  link + ≤280-char excerpt + attribution only; only public facing pages.
- **G5 source-provenance-honest** — a `:mirror` requires `:outlet + :url + :as-of`;
  `:representative` seed is flagged; fabricated coverage is refused (watari freshness).
- **G6 Murakumo-only** — any summary/translation via LiteLLM `127.0.0.1:4000`
  (ADR-2605215000).
- **G7 no-server-key** — actor-event projection + edition publication member/operator-
  signed; `:server-held-key` const false (ADR-2605231525).
- **G8 outward-gated** — live outlet/RSS ingest + live publish = Council Lv6+ + operator.
- **G9 mirror-not-impersonation** — `:article/speak-as` is `:db/allowed [false]`; kawaraban
  mirrors outlets AND actors as observations, never speaks AS them (ADR-2606042330).
- **G10 non-eschatological as-of** — `:news.issue/final` is `:db/allowed [false]`; an
  edition is a dated snapshot, not a last word (非終末論).
- **G11 connective-by-construction (the MEDIUM gate)** — every article is `:mirror` (real
  outlet) OR `:actor-event` (projected first-party Datom); `:original` is not a kind.
  kawaraban authors no first-person claim — it is a medium, not a source (kataribe is the
  primary voice). The article × mention × 面 graph is the actor-to-actor wire.

## Artifacts (R0, all landed)

- **Ontology** `00-contracts/schemas/news-medium-ontology.kotoba.edn` —
  `:news.outlet/* :news.section/* :news.article/* :news.mention/* :news.wire/* :news.rank/*
  :news.issue/*`, with the 11 gates encoded structurally.
- **6 lexicons** `com.etzhayyim.kawaraban.{outlet,section,article,mentionEdge,issue,
  kawarabanReview}` (the article lexicon carries the `const false` invariant fields).
- **5 Pregel cells** (coded state machines; `.solve()` raises `RuntimeError` at R0 —
  live execution is G8-gated): `outlet_ingest` (G4/G5 membrane) · `article_mirror`
  (G1/G4/G9) · `section_route` (G2/G11) · `actor_project` (the medium; G7/G9/G11) ·
  `issue_compose` (G2/G7/G8/G10).
- **Methods**: `route.py` (the medium — actor→面 wire table + the actor-to-actor co-mention
  graph + G1/G4/G9/G11 validate-by-refusal) · `analyze.py` (edition composer — ranks a
  front-面 by G2 public-good signals only; emits `out/edition.md` + derived
  `:news.medium.link/*` edges) · `ingest.py` (offline outlet normalizer; refuses
  full-body/paywall/verdict; `--live` G8-gated).
- **kotoba-wasm**: `wasm/wit/world.wit` (`world kawaraban-actor { export compute: func() ->
  string; }`) — a content-addressed WASI Component-Model component (componentize-py / jco,
  ADR-2606014600); runs browser-local (ameno) AND on donated Murakumo mesh nodes.
- **Murakumo fleet placement** (manifest `murakumoFleet`): 5 cells as k3s DaemonSets across
  the 12-tribe fleet (issachar / asher / dan / naphtali / benjamin).
- **`:representative` seed** `data/seed-news-graph.kotoba.edn` — 7 outlets (NHK / Reuters /
  AP / AFP / Guardian / Al Jazeera / 朝日; Bloomberg-style terminals excluded by G4) / 10 面
  / 9 actor-wires / 12 articles (7 mirror + 5 actor-event) / 24 mention edges.
- **46 tests green** (route 11 + analyze 7 + ingest 8 + cells 20; `./run_tests.sh`).
- **Registered** in `INFRA_ACTORS` → `did:web:etzhayyim.com:actor:kawaraban` (resolvable +
  searchable; surfaces on `/apps` / `/actors` / `/search`).

## Empirical R0 result

`analyze.py` on the seed composes an edition whose **一面 leads** surface the chokepoint
cluster (mitooshi forecast + watari transit + watatsuna cable load), ranked by recency +
source-diversity + actor-relevance only. `route.py` reports the **actor-to-actor wire**:
`watari —4— watatsuna`, `mitooshi —2— watari`, `mitooshi —2— watatsuna`, `danjo —1— ooyake`,
`kanae —1— kanjo` — the medium concretely connecting actor to actor over shared stories.
`ingest.py` refuses the body-bearing, paywalled, and verdict-bearing records in the sample
batch (G4 / G4 / G1), accepting only the two clean public-facing records.

# Consequences

- **Positive**: etzhayyim's `/apps` gains a news face that is, by construction, ad-free,
  surveillance-free, non-adjudicating, copyright-respecting, and non-addictive — a
  public-square mirror that *links out* and a medium that wires the actors together. It
  reuses the feed-post membrane (ADR-2605231902) and the entity-mirror stance
  (ADR-2606042330) rather than inventing a parallel mechanism. ZERO invariant amendments —
  it STRENGTHENS no-server-key, kotoba-canonical-state, and the mirror invariant.
- **Boundaries**: kawaraban is NOT kataribe (kataribe is the primary voice; kawaraban is the
  medium). kawaraban never adjudicates (that is ake/danjo). It never trades or advises (that
  is mitooshi's boundary, which it also respects).
- **Honest R0 limits**: design + datafication + offline composition only. The seed is a
  bounded `:representative` illustrative set (neutral evergreen headlines + example URLs —
  NOT captured real articles, asserting nothing about real events). There is no live
  RSS/outlet ingest, no live publish, no live actor-event projection to the firehose — all
  G8-gated (Council Lv6+ + operator), member-signed (G7). Murakumo-only summary/translation
  is wired at the boundary but not exercised at R0.

# Non-goals (6)

- **N1** NOT a fact-checker / truth adjudicator (G1; ake/danjo own correction & discrepancy).
- **N2** NOT an ad-funded / engagement-optimized feed (G2).
- **N3** NOT a personalized feed / reader-surveillance system (G3).
- **N4** NOT a content republisher — headline + link + fair-use excerpt only (G4).
- **N5** NOT an impersonator — never posts AS an outlet or another actor (G9).
- **N6** NOT a primary source — authors no original claim; mirrors and wires (G11; kataribe
  is the primary voice).

# Roadmap

- **R0** (this ADR, 2026-06-06): ontology + 6 lexicons + 5 cells + medium routing engine +
  edition composer + offline outlet normalizer + kotoba-wasm WIT + Murakumo fleet placement
  + `:representative` seed; 46 tests green. Design + offline only.
- **R1** (post-Council, G8): live-but-gated public-facing-page ingest (open RSS/sitemap of
  public-broadcaster + wire-agency facing pages; no paywall, no full text); live
  actor-event projection wired to the feed-post membrane; Murakumo-only neutral
  summary/translation. Still no ads, no reader profile, no verdict.
- **R2** (post-R1): standing news medium feeding the etzhayyim public timeline; cross-actor
  story clustering; kami-engine 面-layout WASM render on `/apps`.
