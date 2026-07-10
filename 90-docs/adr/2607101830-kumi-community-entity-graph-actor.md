---
id: adr-2607101830-kumi-community-entity-graph-actor
title: "ADR-2607101830: kumi 組 — community/organization-unit dependency-influence-follow-graph + system-dynamics observatory"
status: proposed
doc_type: adr
topic: kumi-community-entity-graph-actor
authoritative: true
last_verified: 2026-07-10
priority: 4.0
axis: architecture
weight: 0.50
priority_note: "Political/religious/cultural/sports/historical COMMUNITY-ORGANIZATION-unit graph — follows/depends-on/influences edges + junkan-style loop classification + kaname-joinable leverage read. Fills the one node-type gap none of kizuna/junkan/kaname/keizu covers: the community itself as a public-role entity."
authoritative_for:
  - 20-actors/kumi
depends_on:
  - adr-2606232200
  - adr-2606172100
  - adr-2605290927
related:
  - adr-2605264000
  - adr-2606272100
supersedes: []
superseded_by: []
---

# ADR-2607101830: kumi 組 — community/organization-unit dependency-influence-follow-graph + system-dynamics observatory

**Status**: proposed
**Date**: 2026-07-10
**Deciders**: Jun Kawasaki

## Context

An owner question surfaced a real gap: does anything in the actor roster model a
**community or organization** — a political group, a local/neighborhood community, a
religious congregation, a cultural society, a historical-preservation society, a sports
club — as a **unit**, with inter-community **dependency**, **influence**, **follow**
relationships, and **system dynamics**?

The answer, after surveying the roster, is *closely adjacent but structurally absent*:

- **kizuna 絆** (ADR-2606232200) graphs actor-to-actor ties, but its node type is
  explicitly **etzhayyim's own actors** (G3 AGENT-only, internal) — not external
  communities, and it is person-excluded by construction.
- **junkan 循環** (ADR-2605290927) runs a society-wide stock/flow causal-loop model, but
  by design (G6) it is **aggregate-only / no individual modeling** — no named entity, let
  alone a named community, is ever a node.
- **kaname 要** (ADR-2606172100) synthesizes leverage across a "power-mirror lineage"
  (tsumugi / keizu / kabuto / chie / shiori / abaki / shionome / busshi / hokorobi /
  kosatsu / inochi) whose node types are public companies, government committee seats,
  AI-ecosystem organizations, commodities, sanctions designations, capital-flow buckets —
  **economic / governmental / AI entities**, not community organizations. kaname's stated
  axes already include "politics / religion / organization / ideology / … " but **no
  observatory in the lineage supplies a community-organization node to compute those axes
  over** — the axis exists; the substrate does not.
- **keizu 系図** graphs government power-relations by **public role** (committee seat,
  ministry, party role) — the closest precedent for "public-role-only, edge-primary,
  non-adjudicating" community modeling, but scoped to state/government relations, not
  civil-society organizations (religious congregations, sports clubs, cultural/historical
  societies).
- **moyoshi 催し** (ADR-2606272100) mints social capital from validated real-world
  gathering ties, but its unit is the **event**, not the standing organization.

No existing actor, and no grep hit for 政治団体 / 宗教団体 / スポーツクラブ /
地域コミュニティ / 文化団体 / 歴史保存 across `20-actors/*/README.md` or
`90-docs/adr/*.md`, covers "community-as-node with inter-community edges." This ADR closes
that gap with a sibling actor, following the exact kizuna-vs-kaname precedent (a distinct
node type gets a distinct actor with its own gates; the meta-synthesizer JOINs it).

## Decision

Add **`kumi 組`** (`20-actors/kumi/`, clj/bb over the kotoba Datom log) — the
**external-community** sibling of kizuna, keizu, and kaname.

組 (kumi) is the plain Japanese word for a bounded, named human group — historically
neighborhood mutual-aid groups (五人組), guild/confraternity structures, and in modern
use a labor union (組合), a sports team, or any registered association — chosen because it
carries no domain bias toward any one of political / religious / cultural / historical /
sports framing; the same word covers all five.

### Position in the ecosystem (extends kizuna's table)

```
kizuna 絆   — INTERNAL: etzhayyim's own actors' social graph (agent-only, person-excluded)
kumi 組     — EXTERNAL: community/organization-unit graph (political/religious/cultural/
              sports/historical/civic groups) — public-role community nodes +
              follows/depends-on/influences edges
kaname 要   — meta-synthesis: leverage over the power-mirror lineage; kumi JOINs as a new
              domain-observatory member, giving the existing politics/religion/organization/
              ideology/… axes an actual community-entity substrate
junkan 循環 — aggregate stock/flow dynamics of society at large (no named entities, ever)
moyoshi 催し — convening: mints social capital from validated real-world gathering ties
keizu 系図  — sibling precedent for public-role-only, edge-primary, non-adjudicating
              relation graphs (government domain; kumi is its civil-society counterpart)
```

### Node type — `:kumi/community`

A **public-role entity only**: `name`, `domain-class` ∈
`#{:political :religious :cultural :historical :sports :civic-neighborhood :labor :other}`,
`jurisdiction-or-locale`, and an optional `public-charter-or-registry-ref`. **Never a
private individual** — mirrors kizuna's G3 (person-excluded) and keizu's G1
(public-role-only, never a private individual). No membership roster is ever ingested or
representable.

### Edge types — kumi's distinctive object, the community-ties graph

- **`:kumi/follows`** — a voluntarily **published** affiliation/membership-of-federation
  declaration (e.g. a local sports club's public charter lists it as a member of a
  national federation; a congregation's public site lists denominational affiliation).
  Community-granularity analogue of kizuna's ATProto follow primitive. Sourced from
  public charters / registries / published affiliation lists only — never scraped private
  directories.
- **`:kumi/depends-on`** — an observed structural/resource dependency (shared venue,
  funding pipeline, leadership pipeline), attributed and **≥2 public-source citations per
  edge** (mirrors keizu's `:rel`/`:money` sourcing discipline and kosatsu's attribution
  discipline).
- **`:kumi/influences`** — an observed **co-occurrence / correlation** tie between two
  communities' public activity, explicitly and structurally labeled non-causal (mirrors
  junkan's G5 "no causal overclaim" and chie's inversion pattern — `:causal-claim` is
  unrepresentable, only `:co-occurrence-observed`).

### System dynamics

kumi feeds a **junkan-style causal-loop model scoped to its own community-subgraph**:
loops = reinforcing (dyad/triad cycles among the three edge types above), classified
exactly like junkan into 好循環 (virtuous) / 悪循環 (vicious) / neutral / transitioning
based on reciprocation density and whether a cycle carries a correlation-only
`:kumi/influences` edge (lower confidence → neutral), plus a Meadows-flavored leverage
read **restricted to structural positions, never a community named as a target**.

### Leverage — kaname JOIN

kumi's community-subgraph is designed to be **joinable** by kaname as a new per-domain
observatory member (alongside tsumugi/keizu/kabuto/chie/shiori/abaki/shionome/busshi/
hokorobi/kosatsu/inochi), the same way kizuna already projects into kaname's
`:actor-society` domain layer. This is the concrete substrate kaname's existing
"politics / religion / organization / ideology / …" axes have been missing. The JOIN
itself is a kaname-side follow-up (R1+, Council-gated live join, same pattern as kizuna's
JOIN) — this ADR only guarantees kumi emits a schema kaname *can* join.

### Constitutional gates (in code + tests, R0)

- **G1 person-excluded.** A `:person/*` / `:sev/human` node is refused at parse — a
  community is a public-role entity, never an individual member or leader (mirrors
  kizuna G3, keizu G1, kaname G1).
- **G2 public-declaration-only sourcing.** Edges are sourced ONLY from voluntarily
  **published** affiliation/charter/registry declarations or ≥2 independent public-source
  citations (mirrors danjo G3 passive-only ingestion, sonae "OPEN feeds only", keizu G3).
  No infiltration, no undercover collection, no scraping of private membership rolls —
  structurally unrepresentable.
- **G3 non-adjudicating / no belief-content.** kumi never encodes doctrinal/ideological
  content and never asserts a belief-verdict; political and religious communities appear
  **only as structural nodes** (mirrors kaname G5 "ideology/religion appear only as
  structural interfaces… never a belief verdict" and danjo G4 non-adjudicating).
- **G4 no-causal-overclaim on `:kumi/influences`.** Correlational/co-occurrence only,
  structurally labeled non-causal (mirrors junkan G5).
- **G5 PROPOSE-not-act / no actuator.** kumi has no actuator at all — like junkan
  ("分析するだけ"), stronger than kizuna/kaname (which at least propose via ossekai): kumi
  emits append-only findings only. If a follow-up intervention is ever warranted it routes
  through kaname → ossekai, never directly from kumi.
- **G6 edge-primary, no per-community power score.** Concentration/leverage is computed
  on read; there is **no stored per-community influence/power score** (mirrors keizu G4).
- **G7 resilience-routing only, never a target-list.** Outputs route to
  interdependency-understanding and resilience, never to "who to pressure / deplatform /
  target" (mirrors kabuto/busshi/abaki's target-list prohibition).
- **G8 Murakumo-only inference, no-server-key.** Standard cross-actor invariant.

G1–G4 are the load-bearing set for this actor specifically, because "political/religious
group influence graph" is adjacent to opposition-research/surveillance risk if built
carelessly — kumi must be at least as conservative as kizuna + danjo + kosatsu + kaname
combined on sourcing and non-adjudication, never less.

## Consequences

- R0 scaffold: `methods/kumi.cljc` (parse community nodes + edges from EDN seed → graph →
  junkan-style loop classification → kaname-compatible leverage read → `beat`, pure +
  deterministic, no actuator cell at all per G5) + `tests/test_kumi.cljc` (**11 tests / 76
  assertions green**, bb; asserts G1 person-node rejection, G2 missing-citation rejection,
  G4 influences non-causal marker + no-causal-field-anywhere-in-output, correct loop
  classification and leverage argmax on the seed) + `data/seed-communities.kotoba.edn` — a
  synthetic, fictional seed spanning **political, religious, sports, cultural, civic-
  neighborhood, labor, and historical** domain-classes, run via
  `bb -cp 20-actors -m kumi.methods.kumi 20-actors/kumi/data/seed-communities.kotoba.edn`
  (and `bb 20-actors/kumi/run_tests.clj` for tests). Seed run: 9 communities, 13 ties,
  5 loops (3 dyad + 2 triad) → regimes `{:virtuous 2 :vicious 1 :neutral 1
  :transitioning 1}`, leverage community (要) = harborview-civic-renewal-local.
- `manifest.edn`: DID `did:web:etzhayyim.com:actor:kumi`, gates G1–G8, non-goals (no
  membership roster, no belief-verdict, no per-community score, no actuation).
- Registered per the repo-wide actor completion condition (CLAUDE.md § Actors): standalone
  repo `etzhayyim/com-etzhayyim-kumi`, west-registered at `orgs/etzhayyim/com-etzhayyim-kumi`
  in the com-junkawasaki superproject, plus a `kumi.identity.journal.edn` RAD identity
  ledger entry under `80-data/kotoba-rad/`.
- **Follow-up (R1):** kaname `:community-graph` domain JOIN (Council-gated, mirrors
  kizuna's `:actor-society` JOIN); live public-registry ingest (G2/G8-gated, offline
  dry-run first, same pattern as watari/kosatsu/danjo).

## Alternatives Considered

1. **Extend kaname directly with a community node type.** Rejected: kaname's existing
   lineage (kabuto/keizu/chie/…) are all economic/governmental/AI entities with their own
   sourcing conventions; folding in civil-society communities would mix gate sets and blur
   kaname's "meta-synthesis over sibling observatories" role. A sibling keeps both
   auditable; kaname JOINs kumi's output — exactly the kizuna-vs-kaname precedent
   (ADR-2606232200 Alternative 1).
2. **Extend kizuna to also graph external communities.** Rejected: kizuna's G3
   (AGENT-only, person-excluded, **internal** actor roster) is a load-bearing boundary;
   external community modeling has a structurally different, more sensitive sourcing
   requirement (G2 above) that does not belong in the internal self-graph actor.
3. **Extend junkan to name entities.** Rejected: junkan's G6 "aggregate-only / no
   individual modeling" is a core invariant precisely because naming entities in a
   society-wide dynamics model raises the surveillance/target-list risk this ADR's G1–G4
   are built to contain; junkan stays anonymous by design, kumi carries the named-entity
   risk in its own, more heavily gated actor.
4. **No new actor — treat this as out of scope.** Rejected: the gap is real (confirmed by
   survey) and the owner explicitly requested design + implementation.

## References

- ADR-2606232200 (kizuna — the internal-actor sibling this pattern mirrors)
- ADR-2606172100 (kaname — the meta-synthesizer kumi is designed to be joinable by)
- ADR-2605290927 (junkan — the system-dynamics idiom kumi's loop classification reuses)
- ADR-2605264000 (ossekai — the consent-bound actuator any future intervention routes
  through, never kumi directly)
- ADR-2606272100 (moyoshi — sibling convening/social-capital actor; event-unit vs kumi's
  standing-organization-unit)
- `20-actors/keizu/` (public-role-only, edge-primary, non-adjudicating precedent)
- `20-actors/kumi/` (methods/kumi.cljc, tests/test_kumi.cljc, data/seed-communities.kotoba.edn)
