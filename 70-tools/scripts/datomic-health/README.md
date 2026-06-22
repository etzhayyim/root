# datomic-ledger fleet health audit

`fleet_audit.clj` — a fleet-level assurance that etzhayyim's actors are **"datomic で設計実装
されている"**: not merely emitting EAVT datoms, but **persisting** them to tamper-evident,
resume-safe, content-addressed append-only **commit-DAGs** with deterministic heartbeats
(ADR-2605312345 / ADR-2605262130).

## Run

```bash
# from the repo root (bb.edn :paths already include 20-actors)
bb 70-tools/scripts/datomic-health/fleet_audit.clj            # full fleet
bb 70-tools/scripts/datomic-health/fleet_audit.clj --actors tate,inochi   # subset
bb 70-tools/scripts/datomic-health/fleet_audit.clj --quiet    # summary line only
```

Pure audit: writes only to `java.io.tmpdir` (throwaway ledgers), touches no actor data,
performs no network I/O (no-server-key). **Exit 1** iff (a) a standard-interface actor violates
an invariant, OR (b) ANY ledger actor's `methods/autorun` or `methods/kotoba` namespace fails to
**load** (a `:load-error` — stale `.clj` shadow, unported fn, broken twin). Every ledger actor
must at least load: this fleet-wide gate catches the bug class fixed in #2021 / #2024 (and the
recurring babashka `.clj`-shadows-`.cljc` prune oversight) continuously. Otherwise **exit 0**.

## What each row proves (over the actor's REAL committed seed)

1. the heartbeat (`methods/autorun` `beat`) appends GROUND datoms to a content-addressed
   append-only commit-DAG (`methods/kotoba` `append-tx`);
2. the chain **verifies** — `verify-chain :ok`, length 1, prev-cid linkage intact (tamper-evident);
3. the beat is **idempotent-by-content** — a second beat over the same seed is a NO-OP
   (`:reason :no-change`), so a recurring loop never bloats the chain;
4. **ground-only** — no derived/transient datom (`:bond/*` / `:ops/*` / `:enkiri/*`) is
   persisted (read-time aggregates are never stored as ground state, N1/G2).

## Two ledger conventions in the fleet

- **standard-interface family** (audited here): exposes `autorun/beat {:tx-id :as-of :log-path}`
  + `autorun/ground-datoms` + `kotoba/verify-chain`, with the commit-DAG machinery vendored
  per-actor (self-contained → pywasm/WASM-portable).
- **non-standard ledger actors** (listed as a **standardization worklist**, not failures):
  sibling / earlier-wave actors that persist via other conventions — e.g. the shared
  `kotoba.datom` library (`chie`, `ugachi`, `busshi`, …), a different `beat` arity, or that
  currently have their own pre-existing load issue. These are reported for visibility; a future
  DRY pass can converge the two conventions.

The audit is intentionally conservative about its exit code: it fails ONLY on a regression in
the standard family, never on the inventory of non-standard actors (whose own `run_tests.sh`
guard their behaviour in CI).
