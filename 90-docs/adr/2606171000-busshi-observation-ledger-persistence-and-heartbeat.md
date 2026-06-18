---
id: adr-2606171000-busshi-observation-ledger-persistence-and-heartbeat
title: "ADR-2606171000: busshi 物資 — content-addressed observation-ledger persistence + idempotent heartbeat (Wave 2)"
status: accepted
doc_type: adr
topic: busshi-observation-ledger
authoritative: true
last_verified: 2026-06-17
priority: 6.0
axis: architecture
weight: 0.55
authoritative_for:
  - busshi observation-ledger persistence (content-addressed append-only commit-DAG)
  - busshi deterministic idempotent-by-content heartbeat (analyze → append on change)
depends_on:
  - adr-2606161730-busshi-commodity-materials-observatory
  - adr-2606170900-ugachi-stewardship-ledger
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605312345-kotoba-datom-first-class-canonical-state
related:
  - adr-2606161800-ugachi-extraction-risk-gate
supersedes: []
superseded_by: []
---

# ADR-2606171000: busshi 物資 — observation-ledger persistence + heartbeat (Wave 2)

**Status**: accepted (landed, clj-native, tests green)
**Date**: 2026-06-17
**Deciders**: Jun Kawasaki

# Context

ugachi 穿ち (the EXECUTION layer) gained a content-addressed, tamper-evident,
idempotent-by-content stewardship ledger (ADR-2606170900). busshi 物資 (the OBSERVE
layer) computed its resilience observations fresh each run and discarded them — no
durable record. This ADR gives busshi the **same** persistence + heartbeat, so both
layers of the §2(l) extraction system record to append-only commit-DAGs (substrate
invariants per ADR-2605262130 / 2605312345). It is a direct mirror of the proven
ugachi machinery, born idempotent (the lesson learned from the ugachi loop, ADR-2606170900).

# Decision

Two clj-native methods (identical machinery to `ugachi.methods.kotoba` / `autorun`):

- **`methods/kotoba.cljc`** — content-addressed append-only OBSERVATION LEDGER:
  `tx-cid` (`"b"+sha256` over canonical JSON `{"datoms":…,"prev":…}`), `make-tx`,
  `tx->edn`, self-contained `parse-edn`, `append-tx`, `read-log`, `head-cid`,
  `verify-chain` (prev-cid chaining → tamper-evident). No-server-key (local file only).
- **`methods/autorun.cljc`** — deterministic, **idempotent-by-content** heartbeat:
  `beat` runs `analyze` over the commodity seed, takes `analyze/datoms` (the analyzer
  refactored to expose the datom **vector** under `datoms`, `render-datoms` now its
  stringifier), and appends one chained tx — UNLESS the observation datoms equal the
  previous beat's, in which case it is a NO-OP (`:appended false :reason :no-change`).
  Caller supplies `tx-id` + `as-of` (no wall clock) → resume-safe.

Ledger lives under gitignored `data/` (`20-actors/busshi/.gitignore`); it is a record
of concentration OBSERVATIONS — **never a target-list** (no mine/well coordinates).

# Consequences

**Positive** — both the OBSERVE (busshi) and EXECUTE (ugachi) layers now persist to
tamper-evident, resume-safe, idempotent commit-DAGs; `analyze/datoms` is reusable; a
recurring loop never bloats the chain. busshi reaches R2 on the substrate invariants.

**Negative / deferred** — observations stay `:representative` (R0 seed); real
primary-source ingest (busshi G7) + Murakumo digest + fleet registration remain Wave 2+.
On the static R0 seed the heartbeat produces exactly one tx then no-ops until the seed
or a real source changes (by design).

# Alternatives Considered

1. **Shared ledger library across actors.** Rejected: the family keeps each actor
   self-contained (its own `kotoba.cljc`) — no cross-actor dependency for the substrate
   primitive (same call made for ugachi).
2. **Persist the markdown resilience map.** Rejected: canonical state is the Datom log
   (ADR-2605312345); persist datoms, render on read.

# References

- ADR-2606161730 — busshi observatory (the observations persisted here)
- ADR-2606170900 — ugachi stewardship ledger (the mirrored, idempotent pattern)
- ADR-2605262130 / 2605312345 — kotoba Datom canonical state
