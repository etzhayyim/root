---
id: adr-2606170900-ugachi-stewardship-ledger-persistence-and-heartbeat
title: "ADR-2606170900: ugachi 穿ち — content-addressed stewardship-ledger persistence + deterministic heartbeat (Wave 2)"
status: accepted
doc_type: adr
topic: ugachi-stewardship-ledger
authoritative: true
last_verified: 2026-06-17
priority: 6.0
axis: architecture
weight: 0.55
authoritative_for:
  - ugachi stewardship-ledger persistence (content-addressed append-only commit-DAG)
  - ugachi deterministic heartbeat (assess → append verdict datoms)
depends_on:
  - adr-2606161800-ugachi-extraction-risk-gate
  - adr-2606161830-ugachi-busshi-grounding-bridge
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605312345-kotoba-datom-first-class-canonical-state
related:
  - adr-2606122400-meisai-card-statement-ingestion
  - adr-2606161730-busshi-commodity-materials-observatory
supersedes: []
superseded_by: []
---

# ADR-2606170900: ugachi 穿ち — stewardship-ledger persistence + heartbeat (Wave 2)

**Status**: accepted (landed, clj-native, tests green)
**Date**: 2026-06-17
**Deciders**: Jun Kawasaki

# Context

ugachi's report calls itself a "stewardship ledger", but the §2(l) gate verdicts were
computed and thrown away each run — there was no durable, auditable record. The
charter values around the substrate (append-only, content-addressed, tamper-evident,
no-server-key; ADR-2605262130 / 2605312345) call for the verdicts to be *persisted* the
same way the meisai/kakaku family persists its data: a local content-addressed commit-DAG.

This ADR makes the stewardship ledger real and adds the autonomous heartbeat that writes
to it — the R2 step both ugachi MATURITY rows flagged.

# Decision

Two clj-native methods (same proven machinery as `meisai.methods.kotoba`):

**`methods/kotoba.cljc`** — content-addressed append-only ledger:
- `tx-cid` = `"b" + sha256-hex` over canonical JSON `{"datoms":[…],"prev":…}` (keys stay
  `:…` strings; EAVT `[op entity attr value]`, op `:db/add` only).
- `make-tx` / `tx->edn` / self-contained `parse-edn` / `append-tx` / `read-log` /
  `head-cid` / `verify-chain` (prev-cid chaining → tamper-evident).
- No-server-key: appends to a LOCAL file only, no network I/O.

**`methods/autorun.cljc`** — deterministic heartbeat:
- `beat` loads projects (+ optional busshi commodities → grounding via the bridge), runs
  the gate, and appends `gate/datoms` (the verdict datoms — `gate.cljc` refactored to
  expose the datom **vector** under `datoms`, with `render-datoms` now its stringifier)
  as one tx chained on the current head.
- Deterministic by construction: the caller supplies `tx-id` + `as-of` (no wall clock,
  no `Math/random`) → resume-safe.
- **Idempotent-by-content**: a beat whose verdict datoms equal the previous beat's is a
  NO-OP — nothing is appended (`:appended false :reason :no-change`). The ledger records
  CHANGES, not a wall-clock liveness tick, so a recurring loop (`/loop 30min ingest`) over
  a static seed never bloats the chain with identical snapshots; it grows only when the
  assessment actually changes. (Observed + fixed during the loop's first session.)

The ledger lives under the gitignored `data/` (`20-actors/ugachi/.gitignore`); it is
generated, never hand-edited, and is a record of extraction DECISIONS — **never a
target-list** (no mine locations; the data is verdicts).

# Consequences

**Positive** — the stewardship ledger is now a durable, tamper-evident, resume-safe
commit-DAG; the heartbeat can run autonomously and compose with the busshi grounding
(grounded beats persist the corrected verdicts). `gate/datoms` is now reusable by any
consumer. Brings ugachi to R2 on the substrate invariants.

**Negative / deferred** — verdicts remain `:synthetic` (R0 seed); the heartbeat is
manual/deterministic (a real scheduler + live kotoba-engine bridge, à la ibuki R3, is a
later operator-gated step). Murakumo-narrated digest + fleet registration remain Wave 2+.

# Alternatives Considered

1. **Persist via a shared library instead of a per-actor `kotoba.cljc`.** Rejected: the
   family deliberately keeps each actor self-contained (meisai/kakaku each carry their own
   reader) — no cross-actor dependency for the substrate primitive.
2. **Persist the full markdown report.** Rejected: the canonical state is the Datom log
   (ADR-2605312345); the report is a render of it. We persist datoms, render on read.

# References

- ADR-2606161800 / 2606161830 — ugachi gate + busshi grounding (the verdicts persisted here)
- ADR-2606122400 — meisai kotoba.cljc (the content-addressed-ledger pattern reused)
- ADR-2605262130 / 2605312345 — kotoba Datom canonical state
