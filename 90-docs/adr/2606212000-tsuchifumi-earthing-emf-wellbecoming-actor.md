---
id: adr-2606212000-tsuchifumi-earthing-emf-wellbecoming-actor
title: "ADR-2606212000: tsuchifumi 土踏み — earthing-EMF Wellbecoming observatory + ossekai actor (clj-native Tier-B)"
status: accepted
doc_type: adr
topic: tsuchifumi-earthing-emf-wellbecoming-actor
authoritative: true
last_verified: 2026-06-21
priority: 6.5
axis: mission
weight: 0.65
authoritative_for:
  - tsuchifumi 土踏み actor (20-actors/tsuchifumi) — the clj-native Tier-B earthing-EMF Wellbecoming observatory
  - the relief-verdict gate (evidence-honest, anti-pseudoscience)
  - the earthing-EMF system-dynamics model (distribution-only)
  - the earthing-EMF risk register + Meadows leverage points
  - tsuchifumi's dry-run atproto おせっかい (ossekai) post invariants
  - tsuchifumi's content-addressed observation-ledger persistence (持続永続化)
depends_on:
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605312345-kotoba-datom-first-class-canonical-state
related:
  - adr-2605264000-ossekai-info-arbitrage-wellbecoming-nudge
  - adr-2606073000-inochi-living-world-kg-mirror
  - adr-2606082102-shiori-wellbecoming-detractor-observatory
  - adr-2605312700-kizashi-noninvasive-body-scan-instrument
  - adr-2606072800-suimin-sleep-disorder-evidence-synthesis
  - adr-2606051800-mitooshi-probabilistic-forecasting-observatory
  - adr-2606111500-hakoniwa-forward-simulation-observatory
supersedes: []
superseded_by: []
---

# ADR-2606212000: tsuchifumi 土踏み — earthing-EMF Wellbecoming observatory + ossekai actor (clj-native Tier-B)

**Status**: accepted (2026-06-21)
**Scope**: `20-actors/tsuchifumi/`
**Deciders**: Jun Kawasaki

## Context

The user asked to: **(1)** analyze and visualize the human-health impact of
electromagnetic-field (EMF) exposure that arises because **earthing / grounding
(アーシング) is not adequately institutionalized worldwide**, **(2)** visualize it
with **system dynamics**, **(3)** analyze the **risk**, and **(4)** design and
implement an actor that performs **ossekai (おせっかい)** over social-proto / atproto.

The roster had no actor for the **environmental-EMF × earthing-access** gap. The
nearest siblings each cover an adjacent slice but not this one:

- **inochi 命** mirrors the biosphere; **shiori 栞** mirrors human Wellbecoming
  detractors (precarity/overwork/isolation/addictive-design) — neither covers
  ambient EMF or the loss of bodily earth contact.
- **ossekai 御節介** is the Wellbecoming-nudge ACTUATOR (AT Proto, consent-bound,
  on-chain-logged); it carries proposals, it does not generate this analysis.
- **kizashi 兆 / suimin 睡眠 / mitate** hold the non-diagnostic + anti-pseudoscience +
  evidence-grading discipline this domain demands.
- **mitooshi 見通し / hakoniwa 箱庭** hold the distribution-only, leak-free,
  non-eschatological forecasting discipline a system-dynamics model must respect.

### The hard problem: this is a scientifically CONTESTED domain

Earthing / grounding therapy and **non-thermal** EMF health effects are **not
established** in mainstream science. The WHO/ICNIRP position establishes **thermal**
exposure limits and treats sub-limit non-thermal harm as not demonstrated; earthing-
therapy clinical claims rest on small, often conflict-of-interest-laden studies. The
field is also saturated with **product fear-marketing** (earthing mats, shielding
devices). An actor here could easily become pseudoscience or a storefront.

The charter forbids both failure modes: **Wellbecoming** + **anti-addictive /
non-manipulative design** (§1.13), the **non-profit / no-commerce** spirit (Rider
§2 collective-commons), and the established non-diagnostic boundary of the care
lineage. The design problem is therefore: **how to act usefully on a real
institutional gap without asserting contested science as fact, without fear, and
without selling anything.**

## Decision

Ship **tsuchifumi 土踏み** (「土を踏む」— treading the earth, the barefoot core of
earthing; also 土踏まず, the arch of the foot) as a **clj-native Tier-B actor**:
an **OBSERVATORY + system-dynamics MODEL + RISK analysis + transparent ossekai
NUDGE**. **Non-diagnostic, non-therapeutic, sells nothing.**

### 1. Epistemic honesty is the defining invariant (G2)

The data model itself separates what is MEASURED from what is HYPOTHESIZED:

- `exposure-load` = 0.40·ambient-emf + 0.35·device-hours + 0.25·indoor-fraction —
  an EXPOSURE fact (:established/:emerging).
- `earthing-deficit` = 1 − weighted(earthing access + institutional grounding) —
  an ACCESS fact (:established), the **institutional gap** the actor names.
- `health-burden` = exposure-load · earthing-deficit — a **HYPOTHESIS**, reported
  ONLY with the `evidence-tier` of its dominant causal pathway and a `confidence`.

The verdict gate (`analyze.cljc`) returns
`{:relief-priority :infrastructure-gap :await-evidence :await-consent :monitor}`.
**A :contested/:anecdotal burden never becomes an asserted harm** — it routes to
`:await-evidence`. The institutional deficit, resting on **established greenspace /
outdoor-time wellbeing evidence**, is always a valid **no-regret** target
(`:infrastructure-gap` / `:relief-priority`) regardless of the EMF debate. A
practice nudge may only rest on ≥:emerging evidence; only the honesty post may NAME
a contested claim, to disclaim it (test-enforced).

### 2. System-dynamics visualization (distribution-only, G6)

`sysdyn.cljc` is a Forrester/Meadows **stock-and-flow** model integrated with
explicit Euler steps. Stocks: **E** ambient-EMF (logistic growth), **A** earthing-
access (tracks infrastructure with lag, eroded by urbanization), **I** grounding-
infrastructure (the POLICY LEVER), **B** the hypothesized burden. It runs a
**parameter-uncertainty ENSEMBLE** (sha256-seeded jitter, no `Math/random`) and
emits **p10/p50/p90 bands only** — a single point forecast is unrepresentable
(`point-forecast` raises). Three scenarios — `:neglect / :baseline / :relief` —
move only the institutional lever; the model shows that **institutionalizing
earthing/greenspace access bends the (hypothesized) burden curve down** (a positive
"relief dividend"), under DISCLOSED parameters. `viz.cljc` renders a **self-
contained HTML** (vanilla canvas, no network) from the REAL method output.

### 3. Risk analysis (evidence-discounted + Meadows leverage)

`risk.cljc` turns the seed's risk DRIVERS into a register
(`risk-score = likelihood · impact · evidence-tier-weight`, shown beside the raw
severity) and a **Meadows leverage-point ranking**. The evidence discount means a
:contested driver (e.g. earthing **product fear-marketing**) cannot dominate on
assertion alone — it lands at the bottom (test-enforced). The leverage ranking
surfaces the highest-leverage **no-regret institutional** intervention (grounding +
greenspace ACCESS standards) over fear-based ones.

### 4. The ossekai actor (social-proto / atproto, G1/G4/G5 + no-server-key)

`social.cljc` drafts **dry-run** `app.bsky.feed.post`-shaped おせっかい nudges. Every
body is SCANNED (disclaimer stripped, shionome pattern) and REFUSED on fear/alarm
(G4), sales/product (G5), diagnosis/treatment (G1), or unhedged EMF-harm assertion
(G2) tokens. Posts are **dry-run only**, **serverHeldKey=false**, and each is a
**proposal routed to ossekai (御節介)**, which CARRIES it consent-bound + on-chain-
logged. tsuchifumi never publishes (the shiori→ossekai division of labour);
`build-live` raises.

### Persistence (持続永続化)

`kotoba.cljc` + `autorun.cljc` are the kafun/ugachi/meisai content-addressed
append-only commit-DAG verbatim in shape: the heartbeat runs analyze + risk →
appends the combined datoms as one content-addressed tx → `verify-chain` tamper-
evident → idempotent-by-content (a no-change beat is a no-op) → resume-safe. No
key, no network I/O.

## Consequences

- The roster gains its first **environmental-EMF + earthing-access Wellbecoming**
  actor, closing a real gap, **without** importing pseudoscience or commerce — the
  honesty layer (G2) and no-commerce layer (G5) are enforced in code + tests, not
  just documented.
- The system-dynamics + risk layers give the org a reusable **stock-and-flow +
  leverage-point** pattern (distribution-only, deterministic) that other actors
  (junkan 循環, kaname 要) can build on.
- All R0 data is `:synthetic`. Real environmental-EMF / public-health / greenspace
  data (G7), live atproto carry via ossekai (G8), DID registration, fleet
  heartbeat, and IPFS/IPNS publication are operator/Council steps.
- **47 tests / 178 assertions green** (babashka): verdict spread, evidence honesty
  (contested never asserted, never relief-priority), risk evidence-discount,
  ossekai guard refusals, distribution-only + point-forecast refusal, ledger
  tamper-evidence + idempotent heartbeat, ontology↔seed parity + negative-space.

## Alternatives Considered

- **Assert EMF/earthing harm and warn people.** Rejected — the science is contested;
  this would be fear-based pseudoscience and violate G2/§1.13.
- **Sell or recommend earthing products/mats.** Rejected — violates the no-commerce
  spirit (G5 / Rider §2); the domain's product-marketing is itself flagged as a
  risk driver pointing the OTHER way.
- **A deterministic point forecast of harm.** Rejected — 非終末論 + mitooshi/hakoniwa
  discipline; the model is distribution-only (G6).
- **Let tsuchifumi post to atproto directly.** Rejected — no-server-key + the
  established shiori→ossekai division: tsuchifumi proposes, ossekai (御節介) carries.

## References

- `20-actors/tsuchifumi/` — actor (manifest, methods, kotoba, viz, tests)
- `90-docs/adr/2605264000-*` — ossekai (御節介) Wellbecoming-nudge actuator
- `90-docs/adr/2606082102-*` — shiori (栞) Wellbecoming-detractor observatory (propose→ossekai pattern)
- `90-docs/adr/2606051800-*` — mitooshi (見通し) probabilistic forecasting (distribution-only)
- `90-docs/adr/2605262130-*` + `2605312345-*` — kotoba Datom log canonical state
