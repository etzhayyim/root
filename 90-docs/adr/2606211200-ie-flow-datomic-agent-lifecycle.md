---
id: adr-2606211200-ie-flow-datomic-agent-lifecycle
title: "ADR-2606211200: Information-energy flow — a kotoba/co-scientist agent lifecycle every actor embeds"
status: accepted
doc_type: adr
topic: ie-flow-datomic-agent-lifecycle
authoritative: true
last_verified: 2026-06-21
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - etzhayyim.ie-flow
depends_on:
  - adr-2606201200-ibuki-coscientist-entropy-react-loop
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605241500-dataset-cid-substrate
related:
  - adr-2606101200-ibuki-organism-autonomy
  - adr-2605215000-etzhayyim-inference-murakumo-only
supersedes: []
superseded_by: []
---

# ADR-2606211200: Information-energy flow — a kotoba/co-scientist agent lifecycle every actor embeds

**Status**: accepted
**Date**: 2026-06-21
**Deciders**: Jun Kawasaki

# Context

The founder sketched an **information-energy flow** design: put the immutable atomic FACTS — events,
nodes, edges, stocks, interventions, model runs — in a Datomic-style ledger, and do the CALCULATION
in pure Clojure functions (entropy / **order-index** = how much scattered flow was rectified onto
outcomes / **net-gain** = value − cost − risk / **agent-efficiency** = the「課金される魔法陣」test),
with system-dynamics and agent-simulation as pure folds. The ask: realise this on **kotoba**, fuse it
into the **artificial-organism react loop** with the **Google AI co-scientist**, store **real-world
data as EDN, measured, into DataLad**, and **embed it into every actor as a system of systems**.

This maps cleanly onto existing substrate. The etzhayyim boundary already says canonical state = the
kotoba Datom log (content-addressed EAVT, append-only, ADR-2605312345) and the logic = pure folds
over it. ibuki already runs the co-scientist (Generate→Reflect→Rank→Evolve→Meta-review) as the
organism's cognition over a metabolic state vector (Φ/η/surprise, ADR-2606201200). What was missing:
(1) the explicit **flow ledger** (events→edges→nodes→stocks→interventions) and the **order calculus**
(order-index / net-gain / agent-efficiency) as first-class, actor-agnostic measurements; (2) a
**reusable library** so the loop is not a per-actor fork; (3) a **real-world ingest → EDN → DataLad**
path; (4) an **embedding contract** that makes the actor roster a system of systems.

# Decision

Ship **`etzhayyim.ie-flow`** (`70-tools/src/etzhayyim/ie_flow/`, clj/bb, the operational-code
convention) — one shared library every actor embeds:

- **`metrics`** — entropy, `order-index`, `net-gain`, `agent-efficiency`, `aggregate-flows`,
  `flow-state` (the SENSE state vector), faithful to the founder's formulas.
- **`ledger`** — events/nodes/stocks/interventions on the kotoba commit-DAG (append-only, numbers
  milli-scaled for CID determinism); `read-events` round-trips the facts back for the metric folds.
- **`dynamics`** — `step-system` / `simulate` / `counterfactual` over accumulated-order stocks.
- **`coscientist`** — the Google co-scientist GENERALISED over the flow metrics (fitness =
  Δnet-gain + Δorder-index, 子孫-weighted, per cost). Generation is a charter-clean **catalog**, never
  an LLM free-write; the **same aligned/forbidden mechanism vocabulary as ibuki** is shared and
  unforkable, so the whole system of systems carries one safety property: a predatory mechanism is
  structurally unrepresentable. Murakumo narrates only the meta-review (fail-open template, G6).
- **`lifecycle`** — the SENSE→ORIENT→…→PERSIST beat: pre-register a DRY-RUN experiment (prediction
  recorded before the outcome — leak-free, the mitooshi discipline), Brier proper-score the prior
  beat against the now-observed net-gain, update a per-mechanism kaizen weight, persist one
  content-addressed tx (idempotent-by-content, verify-chain, resume-safe; logical time = log length).
- **`ingest`** — real-world data → EDN → DataLad: `:git` makes the **monorepo measure its own
  development metabolism** (each commit = a flow event; AI authors → `:agent?` so agent-efficiency is
  real), plus a generic `:edn-events` source. The snapshot (`flow.kotoba.edn`) + `ingest-provenance.json`
  are committed under `80-data/ie-flow/<source>/` (jinushi/genome load-discipline: the snapshot is the
  source of truth, the loop re-measures with zero network I/O).
- **`embed`** — the system-of-systems entry point: `record!` / `measure` / `beat!` (3-line adoption)
  + an `actor-registry`. Per-actor ledgers live under `80-data/ie-flow/<actor>/`.

The charter gates are unchanged from ibuki and tested: **G-parasitism** (projected order ≥ floor),
**G-subordinate** (子孫 wellbecoming ≥ 0), **G-mechanism** (aligned-only), **G-falsifiable**,
**G-leash** (outward = member-principal / dry-run; no-server-key). No invariant is amended.

# Consequences

- **Verified**: 27 tests / 80 assertions green (bb). Real ingest run: 273 commits → 8 layer-edges,
  order-index 0.634, net-gain > 0, chain-verified — committed to `80-data/ie-flow/repo-git/`.
- Each actor gains a measured flow + a reasoning loop for ~3 lines, sharing the safety property.
  The `registry.edn` roster (ibuki/tsumugi/shionome/kaname/okaimono seeded) grows as actors adopt —
  the same shared-lib-plus-registry pattern the rest of the roster uses, not 80 forks.
- ibuki's organism-specific co-scientist (ADR-2606201200) is the special case (its metabolism IS an
  information-energy flow); this generalises it without disturbing it.
- Live legs stay gated: Murakumo narration (G6, injected), live persistence to the kotoba engine
  (reuse the ibuki R3 bridge, G7), and outward interventions (member-principal). The loop itself does
  no network I/O and holds no key.

# Alternatives Considered

- **Fork the loop into each actor** — rejected: ~80 divergent copies, no shared safety property.
- **A separate analytics DB (RisingWave/Postgres)** for the flow ledger — rejected: violates the
  substrate boundary; the Datom log already gives as-of history + content-addressing + crash-resume.
- **Let the co-scientist free-write interventions via the LLM** — rejected: a predatory mechanism
  must be unrepresentable, so generation stays a charter-clean catalog (LLM narrates, never generates).

# References

- `70-tools/src/etzhayyim/ie_flow/` (library + README + tests)
- `80-data/ie-flow/` (registry + measured `repo-git` snapshot + provenance)
- ADR-2606201200 (ibuki co-scientist entropy ReAct loop — the special case generalised here)
- ADR-2605312345 (kotoba Datom log = first-class canonical state)
- ADR-2605241500 (DataLad/IPFS dataset CID substrate)
