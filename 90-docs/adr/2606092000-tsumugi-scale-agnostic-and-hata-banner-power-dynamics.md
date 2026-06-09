---
id: adr-2606092000-tsumugi-scale-agnostic-and-hata-banner-power-dynamics
title: "ADR-2606092000: tsumugi 紡ぎ — scale-agnostic 産官学報 concentration (A) + 旗 hata ideology/faction dimension (B)"
status: proposed
doc_type: adr
topic: tsumugi-scale-banner-power-dynamics
authoritative: true
last_verified: 2026-06-09
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - tsumugi-scale-agnostic-power-dynamics
  - tsumugi-hata-banner-ideology-faction
depends_on:
  - adr-2606011800-tsumugi-spirit-intel-power-graph
  - adr-2606061500-tsumugi-diachronic-influence-history
  - adr-2606011000-engi-knowledge-graph
  - adr-2606011500-spirit-ontology
  - adr-2605081300-edge-primary-karma
  - adr-2606042330-entity-as-actor-mirror
  - adr-2606066000-keizu-government-power-relations
  - adr-2605262130-kotoba-storage-substrate-unification
related:
  - adr-2606073100-abaki-anti-monopoly-intelligence-membrane
  - adr-2605301600-danjo-public-accountability
  - adr-2605302300-kanae-fiscal-flow-visualization
supersedes: []
superseded_by: []
---

# ADR-2606092000: tsumugi 紡ぎ — scale-agnostic 産官学報 concentration (A) + 旗 hata ideology/faction dimension (B)

**Status**: proposed
**Date**: 2026-06-09
**Deciders**: Jun Kawasaki

# Context

The power-mirror lineage (tsumugi 紡ぎ / keizu 系図 / danjo 弾正 / kanae 鼎 / tadori 辿 /
ooyake 公 / kabuto 兜 / kosatsu 高札) already weaves **global power dynamics**. An audit
against the founder ask — *「地域・国・思想・組織ごとの意識的な power dynamics もすべて
精微か。例えば長崎では三菱の方、県庁の人、長崎新聞のやつなどの local dynamics」* — found
two real gaps, and one constitutional boundary that the ask brushes against:

1. **Scale gap (A).** tsumugi's seed power-graph is implicitly **national / corporate-
   keiretsu** scoped. The same 取-concentration lens is never run at the **local / regional /
   intra-org** scale, nor over **academic societies (学会)** as power collectives. The 長崎
   case — 三菱重工長崎造船所 (産) ↔ 県庁＋審議会 (官) ↔ 長崎大学 (学) ↔ 長崎新聞 (報),
   a tightly co-woven local 産官学報 fabric — was *expressible as org nodes but not surfaced*.

2. **Ideology gap (B).** tsumugi's diachronic extension (ADR-2606061500) models thought-
   **streams** through history but never projects them into the **present** as the
   *意識的* (conscious / declared) axis of alignment: which ideological **banner** today's
   public-power entities openly fly, and how present factions descend from historical 思潮.

3. **Constitutional boundary.** The founder's phrasing *「三菱の方、県庁の人、新聞のやつ」*
   reaches for **named private individuals**. tsumugi G1 + keizu G1 (no-doxxing) make a
   private person **unrepresentable by construction** — only public **seats** (議長/委員/
   首長/編集委員) and institutions are nodes. This ADR does **not** weaken that; it makes the
   *seat/institution-level* local + ideological dynamics precise while keeping persons out.

Per the founder's structural decision (this session), (A) and (B) are delivered as
**extensions to tsumugi/keizu — NO new actor** — mirroring how ADR-2606061500 extended
tsumugi in place. (B) is named **旗 (hata)** — the banner an entity flies its colours with.

# Decision

Two in-place extensions of tsumugi (`20-actors/tsumugi/`), each a new ontology + seed +
stdlib analyzer + tests, wired as new manifest cells.

## (A) Scale-agnostic 産官学報 concentration

- **Ontology** `00-contracts/schemas/power-scale-ontology.kotoba.edn`: `:pwr/*` nodes carry a
  `:pwr/scale` (`:global → :supranational → :national → :regional → :local → :intra-org`) and a
  `:pwr/sector` (`:san 産 :kan 官 :gaku 学 :hou 報 :min 民 :kin 金`) and a `:pwr/locality`
  cluster key; `:tie/*` are the first-class factual 縁.
- **Analyzer** `methods/analyze_scale.py` (pure stdlib): per-**locality** and per-**scale**,
  computes the **edge-primary integral of cross-sector co-location** — `concentration =
  Σ(cross-sector :tie/grasping-load) × sector-diversity` — plus cross-sector **brokers** (as
  seat/org ids). The **same lens at every scale**: the 長崎 local cluster and a national
  keiretsu are ranked by one metric.
- **Seed** `data/seed-scale-power.kotoba.edn`: three instances at three scales — (1) 長崎
  local 産官学報 (the flagship), (2) a 学会 intra-org board/journal/sponsor, (3) a national
  keiretsu — all `:representative`, structural-public facts only.
- **First run**: `jp.nagasaki` surfaces as the top cluster (all 4 産官学報 sectors woven,
  concentration 12.08; 三菱重工長崎造船所 the top cross-sector broker, span 3).

### Five invariants (S1–S6, enforced in three sites each — `:db/allowed` + analyzer `ValueError` + test)
- **S1 edge-primary** — concentration on `:tie/grasping-load` only; no `:pwr/power-score` (raises).
- **S2 person-excluded** — `:pwr/standing ∈ {:institutional :public-seat}`; `:private-person` raises.
- **S3 aggregate-first** — per-locality/per-scale aggregates; brokers are seat/org ids.
- **S4 sourcing honesty** — every `:tie` ≥2 public citations; under-sourced raises.
- **S5 non-adjudicating** — verdict tokens (`:癒着 :談合 :capture …`) unrepresentable (raises).
- **S6 map-not-target** — an openness/resilience map routed to opening, never a target-list.

## (B) 旗 hata — ideology / faction dimension

- **Ontology** `00-contracts/schemas/banner-ontology.kotoba.edn`: `:banner/*` (a descriptive
  standard, kind ∈ `:political-platform :doctrinal :school-of-thought :policy-stance`, optionally
  linked to a historical `:banner/thought-stream`), `:ent/*` (public org/seat/self), `:flies/*`
  (the alignment 縁, with a `:flies/basis` that is always **on-the-record**).
- **Analyzer** `methods/analyze_banner.py` (pure stdlib): present-day **camps** (per-banner
  reach = Σ incident `:flies/weight`), **bridges** (entities flying ≥2 banners — pluralism),
  and **genealogy** (banner ← historical thought-stream).
- **Seed** `data/seed-banner.kotoba.edn`: abstract textbook 主義 banners tied to streams +
  **self-declared** public party platforms on the 改憲↔護憲 axis + the **etzhayyim self-node**
  flying its own Charter banner inbound-only. It deliberately does **not** label corporations /
  newspapers / persons with ideologies (highest defamation risk) — that stays G7-gated.

### The thought-policing guard (H1–H7) — why representing ideology is safe here
- **H1 public-declared basis only** — `:flies/basis ∈ {:self-declared :public-stated
  :voting-record :formal-membership}`; `:inferred/:suspected/:imputed` raise. No hidden/"real" ideology.
- **H2 non-adjudicating** — threat tokens (`:extremist :過激 :危険思想 :terrorist …`)
  unrepresentable; no `:banner/threat-level`, no `:ent/loyalty`.
- **H3 edge-primary** — alignment on `:flies/*` only; no `:ent/ideology-score`/`:conviction` (raises).
- **H4 person-excluded** — `:flies/who` institutional/public-seat/self only; not a belief registry.
- **H5 mirror + symmetric** — etzhayyim discloses its **own** banner (inbound-only); it does not
  judge from a pretended neutral.
- **H6 plural + contested** — many-to-many; ≥2-banner entities are bridges, not anomalies.
- **H7 sourcing** — every `:flies` ≥2 public citations (the entity's own manifesto/statement/vote).

# Consequences

- The founder's 長崎 question is answerable at the **seat/institution level**: the local
  産官学報 weave is now a first-class, ranked, edge-primary observation — and the **same lens**
  runs over 学会・会社・法人 at any scale. The *named-individual* layer remains out by
  constitutional design (G1 no-doxxing); this is stated, not silently dropped.
- (B) makes ideology representable **without** becoming a thought-registry: declared-only,
  non-adjudicating, edge-primary, person-excluded, plural — the highest-risk extension carries
  the strictest gates (H1–H7), guarded in three sites each + 11 tests.
- 22/22 new tests green (11 scale + 11 banner). No new dependency (pure stdlib, pywasm-ready).
  No change to existing tsumugi behaviour (additive cells).

**Honest scope (R0 design-only):** `:representative` bounded seeds (not exhaustive, not
authoritative); the 学会X / 政党A·B·C entities are representative placeholders, not assertions
about specific named organizations; grasping-load/weight are illustrative, not measured. Live
planet-scale ingest of localities and entity↔banner alignment (voting records / manifestos at
scale, atproto, local registries) is **G7 + Council + operator-gated** (unbuilt). Murakumo-only
narration (G6). No published social post.

# Alternatives Considered

- **New sibling actors (地脈 + 旗).** Rejected per founder structural choice — extend
  tsumugi/keizu in place; avoids roster sprawl + overlap with keizu's government object.
- **Region-only (A).** Rejected — founder broadened (A) to *汎用: 学会・会社・法人・組織
  すべて*. Hence the scale axis is fully general, not a Japan-prefecture special case.
- **Inferred ideology (B).** Rejected outright — imputing a hidden ideology is the exact
  thought-policing failure mode; H1 makes it unrepresentable.
- **Individual-level local dynamics.** Rejected — violates G1 no-doxxing (constitutional).

# References

- `90-docs/adr/2606011800-tsumugi-spirit-intel-power-graph.md` (tsumugi base)
- `90-docs/adr/2606061500-…-diachronic-influence-history.md` (thought-streams, extended here)
- `90-docs/adr/2606066000-keizu-government-power-relations.md` (sibling; G1 no-doxxing)
- `00-contracts/schemas/power-scale-ontology.kotoba.edn` · `…/banner-ontology.kotoba.edn`
- `20-actors/tsumugi/methods/analyze_scale.py` · `…/analyze_banner.py`
