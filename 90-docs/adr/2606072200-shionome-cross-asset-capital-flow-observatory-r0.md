---
id: adr-2606072200-shionome-cross-asset-capital-flow-observatory-r0
title: "ADR-2606072200: 潮目 (shionome) — cross-asset capital-flow observatory (ingest · intel · analyze · dry-run social, NO trading) R0 + autonomous kotoba loop"
status: accepted
doc_type: adr
topic: shionome-cross-asset-capital-flow-observatory
authoritative: true
last_verified: 2026-06-07
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - shionome-cross-asset-capital-flow-observatory
  - capital-rotation-flow-graph
  - no-trade-non-advisory-market-observation
depends_on:
  - adr-2606051800-mitooshi-probabilistic-forecasting-observatory
  - adr-2606071000-intel-osint-actor-cohort-r1-and-fleet-readiness
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605231525-server-side-signing-capability-boundary
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
related:
  - adr-2605302300-kanae-government-fiscal-flow-visualization
  - adr-2606032000-kanjo-company-financial-disclosure-graph
  - adr-2606041827-watari-live-ship-aircraft-position-graph
  - adr-2606022000-kabuto-supply-chain-knowledge-graph
  - adr-2606066000-keizu-government-relations-graph-tier-b-actor-r0
supersedes: []
superseded_by: []
---

# ADR-2606072200: 潮目 (shionome) — cross-asset capital-flow observatory R0

- **Status**: accepted
- **Date**: 2026-06-07 (JST)
- **Deciders**: founder seat (intel-loop wave)
- **Supersedes / amends**: none — ZERO invariant amendments

## Context

A standing ask: *「株式・コモディティ・国際・暗号資産・不動産の価格変動から、どこからどこへ
資金が流れているかを ingest / intel / analyze して social post する actor。ただしトレードは
しない。」* — observe where capital rotates across the world's asset classes and narrate it, but
**never trade**.

The intel/OSINT cohort already covers adjacent objects: **mitooshi** forecasts (distribution-only,
never trades), **kanjo** mirrors company financial *disclosure*, **kanae** renders *government*
fiscal flows, **watari** tracks live physical positions, **kabuto** maps supply-chain
concentration. None of them observes **cross-asset capital rotation** — the realized movement of
money between equities / bonds / credit / commodities / FX / crypto / real-estate / cash. That is a
distinct object, and a dangerous one: a "where is money flowing" tool is one careless step from a
"what should I buy" tool. The charter requires that step be **structurally impossible**, not merely
discouraged.

## Decision

Introduce **潮目 (shionome)**, a Tier-B cross-asset capital-flow observatory, at **R0**:
ontology + 4 lexicons + a `:representative` seed + an offline analyzer + a kotoba Datom-log writer
+ an **autonomous heartbeat loop** + 5 cell scaffolds + tests. It models the world's capital as a
graph of public **buckets** (asset-class / sector / region / theme) and **flows** (observed
capital movement), computes aggregate edge-primary metrics (net flow per bucket, rotation pairs,
inflow HHI, by-asset-class / by-region, a factual regime descriptor), and narrates **dry-run**
social posts.

### The defining invariant — トレードはしない (G2, no-trade / non-advisory)

shionome NEVER emits a buy/sell signal, a price target, an over/under-weight call, or any
portfolio instruction. This is enforced in **four homes**:

1. **Ontology** — trade/advisory tokens are not enum members of `:ontology/flow-kinds`; there is
   no `:bucket/rating`/`:signal`/`:target`/`:score` attribute (a rating *is* a trade instruction).
2. **Lexicons** — `noTradeNotice` is `:const true` on `capitalFlowObservation` / `rotationFinding`
   / `networkPost`.
3. **`weave.TRADE_TOKENS`** — refused on every flow + bucket kind (`validate_flow`/`validate_bucket`).
4. **`social._guard_no_trade`** — every post body is scanned and refused if a trade token appears.

`test_charter_invariants.py` parses the data homes and asserts they agree, so weakening the rule in
one place fails the suite.

### The 11 gates

G1 public-bucket-only / no-doxxing · **G2 no-trade / non-advisory** · G3 ≥2 public sources
(commercial terminals prohibited, Rider §2(e)) · G4 edge-primary, no per-asset rating · G5
mirror-not-signal · G6 Murakumo-only · G7 no-server-key · G8 outward-gated · G9 PII-encrypted ·
G10 non-eschatological append-only as-of · G11 sourcing-honesty. (Full text in
`20-actors/shionome/CLAUDE.md` + `manifest.jsonld`.)

### Autonomous operation on kotoba (「自律的に稼働」)

`methods/autorun.py` runs the full pipeline by itself each heartbeat —
observe → validate → weave → aggregate → dry-run post → **persist a content-addressed transaction
to the append-only kotoba Datom log** (`methods/kotoba.py`). The log is a verifiable commit-DAG
(each tx links the previous tx's CID; tampering breaks `verify_chain`), append-only (G10), and
deterministic (cycle index drives tx-id + as-of, so a re-run reproduces the same head CID). This is
autonomy in the **charter-permitted** form: the actor drives its own observe→analyze→persist cycle
over its own substrate, with **no live external I/O**. Per ADR-2606071000, that is the reachable
goal — "deploy-ready", with the single remaining step being a **human gate flip** (G7/G8) to enable
live market-data ingest + live external posting.

### kotoba-WASM component + Murakumo-fleet cron cells (deploy-readiness)

The autorun loop above is the off-fleet self-driving demonstrator. Its **production form** is two
concrete kotoba-WASM artifacts, both empirically built/verified off-fleet:

1. **Standalone WASI component** (`20-actors/shionome/wasm/`) — `app.py` + `wit/world.wit` built
   with **componentize-py** into `shionome-actor.wasm` (18.5 MB, WASI Preview 2),
   `wasm-tools validate` clean, **jco-transpiled and executed under node** (`node verify.mjs` →
   `regime=risk-on`, `no_trade=true`). CID
   `bafybeigk6whellozcybop4btzcrdtybd5yejjrax7tczxhapfsyya64hka` (dag-pb → T2 donated-mesh, bundles
   CPython). The `.wasm` + `transpiled/` are gitignored, reproducible from source via `build.sh`.

2. **5 Murakumo-fleet cron cells** (`20-actors/magatama/cells/shionome_*`) — `kotoba_langgraph`
   Pregel cells ("Resident in Kotoba WASM", the ossekai precedent), each shipping a
   `cells.toml.fragment` with `trigger = { kind = "cron", … }` on a real fleet node: `ingest`
   (issachar `5 * * * *`), `flow_graph` (issachar `10 * * * *`), `rotation_weave` (dan
   `15 * * * *`), `regime_observer` (dan `20 * * * *`), `social_post` (naphtali `0 9 * * *`).
   Registered in `50-infra/murakumo/fleet.toml` (node↔cell) + discovered by `cell_runner_main.py`
   (added the `shionome_*` fragment glob). Pure logic in `shionome_core.py` (no `kotoba_langgraph`
   dependency), tested off-fleet (**14/14** in `test_shionome_cells.py`).

The cells run as **k3s DaemonSet Pods** via the Ansible playbook
`60-apps/etzhayyim-project-murakumo/ansible/k8s-gpu-cluster.yml`. The actual `ansible … deploy`
onto the physical Mac-mini fleet is the **operator** step — an agent cannot execute it
(ADR-2606071000). Cron cells fire the analyze→dry-run cycle over substrate-resident data; live
market-data ingest + live external posting remain G8-gated.

### Stock layer (R1 addendum, 2026-06-09) — the money-and-markets pyramid

The R0 graph is **flow-first** (edge-primary): it answers *where capital moved*, but not *how big
each pool is*. To cover the Visual-Capitalist "All of the World's Money and Markets in One
Visualization" view — the proportional SIZING of every asset class against each other — the
snapshot mechanism is extended with one metric rather than a new entity type:

- **`:outstanding-usd`** is added to `:ontology/snapshot-metrics` / `:snap/metric` (and its three
  homes: ontology `:db/allowed`, `bucketSnapshot` lexicon `:enum`, `weave.SNAPSHOT_METRICS`). It
  records the observed total SIZE (stock) of a bucket in **USD trillions**.
- **`weave.stock_pyramid`** aggregates the *latest* `:outstanding-usd` snapshot per bucket up to the
  asset-class level and sizes each layer against the grand total — the money pyramid (physical
  currency < broad money < equities < debt < real estate < derivatives notional, with gold/crypto
  sized against them). The `:representative` seed adds 8 global layers totalling **1,383 tn**.
- **Why this does NOT weaken any gate**: a SIZE is a factual observed quantity, exactly like
  `:return-pct` / `:yield-pct` — it is descriptive, carries `no_trade_notice=true`, and is **not** a
  per-asset rating / signal / target (G2/G4 untouched; `:bucket/rating` et al. remain
  unrepresentable). Stock (usd-tn) is computed on a **separate** read path and is never summed with
  flow magnitudes (usd-bn) — a unit guard, not a new capability. The no-trade boundary is unchanged:
  shionome now says how large each pool of capital is, still never what to do with it (トレードはしない).

## Consequences

- **Positive**: a new, distinct cross-asset capital-rotation lens for the commons; a hard,
  test-pinned no-trade boundary that makes a robo-advisor structurally unrepresentable; a working
  autonomous loop that materializes a content-addressed Datom artifact (deploy-ready); clean
  hand-offs to kanae (render) and mitooshi (forecast input).
- **Costs / risks**: the `:representative` seed is illustrative, not authoritative (G11) — readers
  must not mistake it for live data; live ingest/posting needs Council Lv6+ + operator (by design).
- **No invariant amendments**: shionome reuses existing constitutional invariants (Murakumo-only,
  no-server-key, kotoba-canonical, Rider §2(e), non-eschatological) and adds the no-trade gate as a
  per-actor structural constraint.

## Alternatives Considered

- **Fold into mitooshi** — rejected: mitooshi forecasts distributions; shionome observes realized
  flows. Conflating realized-observation with forecast would muddy mitooshi's leak-free scoring.
- **Allow over/under-weight "positioning" language** — rejected: positioning is advisory; the
  no-trade boundary must be bright-line. Only descriptive flow language is permitted.
- **Permit a commercial market-data terminal as a source** — rejected (Rider §2(e)/N5): a
  capital-flow commons built on a paywalled terminal re-introduces the asymmetry it exists to
  dissolve.

## References

- `20-actors/shionome/` — actor (manifest, CLAUDE.md, methods, lex, cells, registry, data)
- `00-contracts/schemas/capital-flow-ontology.kotoba.edn` — ontology (closed-vocab SSoT)
- ADR-2606051800 (mitooshi), ADR-2606071000 (intel cohort deploy-readiness), ADR-2605312345
  (kotoba Datom canonical state), ADR-2605215000 (Murakumo-only), ADR-2605231525 (no-server-key)
