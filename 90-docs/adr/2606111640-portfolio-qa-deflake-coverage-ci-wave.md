---
id: adr-2606111640-portfolio-qa-deflake-coverage-ci-wave
title: "ADR-2606111640: Portfolio QA wave — SDK quorum-test deflake, kotoba coverage baseline + CI"
status: accepted
doc_type: adr
topic: portfolio-qa-deflake-coverage-ci-wave
authoritative: true
last_verified: 2026-06-11
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - sdk-test-determinism
  - kotoba-coverage-baseline
depends_on:
  - adr-2605231400-kotoba-datomic-holochain-iso-substrate
  - adr-2605262130-kotoba-storage-substrate-unification
related:
  - adr-2605302355-kotoba-langgraph-llm-verified-durable-routing
supersedes: []
superseded_by: []
---

# ADR-2606111640: Portfolio QA wave — SDK quorum-test deflake, kotoba coverage baseline + CI

**Status**: accepted
**Date**: 2026-06-11
**Deciders**: Jun Kawasaki

# Context

A cross-project maturity audit (2026-06-11) found the portfolio's verification
layer lagging far behind its design layer:

1. **`@etzhayyim/sdk` was believed red.** `.github/workflows/test.yml` carried a
   note that the suite fails on the incomplete libsignal→XChaCha20 migration in
   `src/encrypted.ts` (a590e7f64). In fact that migration break was already
   resolved; the only real failure was a **flaky assertion** in
   `test/kotoba-datomic-witnessed-write.test.ts` ("3 accept + 2 reject" quorum):
   it asserted `minority` has exactly 2 entries, but `collectQuorum`
   intentionally returns as soon as the 3rd accept arrives (documented
   early-exit) and the in-memory transport delivers attestations
   fire-and-forget in nondeterministic order — so 0..2 rejects may have been
   collected at decision time.
2. **kotoba (40-engine/kotoba, standalone etzhayyim/kotoba) had no coverage
   measurement and no CI.** ~2,100 lib tests existed and were green, but were
   only ever run by hand at ~150 commits/week; no number existed for "what is
   actually covered".
3. The first instrumented run **flushed out a date-rot time bomb**:
   `kotoba-server pre_proxy::operator_trusted_pre_roundtrip_end_to_end` used a
   hardcoded `issued_at: 2026-05-31` CACAO with no expiry, so the 7-day
   `MAX_CACAO_AGE_SECS` cap made it fail from 2026-06-07 onward — the same bug
   class the happy-path fixture in that file had already been fixed for.

# Decision

1. **Deflake, don't weaken**: the quorum test now asserts the semantics the
   implementation guarantees — exactly 3 all-`accept` `matching`, `minority`
   ≤2 and all-`reject` — instead of an arrival-order-dependent count. The
   stale libsignal break notes in `test.yml` are corrected, and the SDK
   `package-lock.json` is synced with `package.json` (`@noble/hashes ^1.8.0`;
   the lock still pinned the pre-migration `^2.2.0` manifest entry).
   (root PR #1613; `sdk-test` green in CI.)
2. **kotoba gets a repeatable coverage harness**: `scripts/coverage.sh`
   (cargo-llvm-cov; `summary` / `html` / `lcov` modes), pinned to
   `rustup run stable` because Homebrew rust ships no llvm-tools. Documented in
   kotoba README §Coverage. **First measured baseline (workspace lib tests,
   2026-06-11): 78.75% line / 79.37% region / 76.05% function.**
   (kotoba PR #104.)
3. **kotoba gets CI**: `.github/workflows/test.yml` runs
   `cargo test --workspace --lib` on every PR + push to main with rust-cache.
   The repo's `.cargo/config.toml` pins `build.target = aarch64-apple-darwin`
   for local Apple Silicon dev, so CI passes the runner's host triple via an
   explicit `--target` to build natively. (kotoba PR #105.)
4. **CACAO test fixtures must not date-rot**: a fixture CACAO either derives
   `issued_at` from now or carries an explicit far-future `expiry`
   (`2099-12-31T23:59:59Z`), never a hardcoded `issued_at` with `expiry: None`
   (which inherits the 7-day max-age cap). Applied to the `pre_proxy` e2e
   fixture; this is the standing rule for new fixtures.

# Consequences

- The SDK suite (188 tests) is deterministic: 3 consecutive full runs green
  locally, `sdk-test` green on PR CI. The "known pre-existing break" framing
  is gone from `test.yml`, so a red `sdk-test` is a real regression again.
- kotoba coverage is now a measured number, not an estimate. Honest low spots
  recorded with the baseline: kotoba-clj / kotoba-ingest / b2_* store paths at
  0% in lib-test scope, kubo_store 37%, wasm_pregel 47%, signal_xrpc 57%.
- kotoba regressions are caught on PR instead of by hand. Kubo-dependent
  integration tests and fmt/clippy gates are deliberate follow-ups (the tree
  is not fmt-clean yet).
- Known pre-existing break surfaced in passing, NOT fixed here:
  `tsc (20-actors/mst-projector)` fails on `main` because
  `@etzhayyim/yorishiro-huggingface-inference-mcp` is declared `workspace:*`
  but exists nowhere in the monorepo (noted on PR #1613).

# Alternatives Considered

- **Make the in-memory witness transport deterministic** (ordered delivery)
  instead of relaxing the assertion — rejected: it would test an ordering the
  real PDS-firehose transport does not provide, hiding the race instead of
  acknowledging it.
- **cargo-tarpaulin** instead of cargo-llvm-cov — rejected: llvm-cov is the
  toolchain-native instrumentation (branch-accurate, works with the pinned
  wasmtime build graph) and was already installed.
- **Full `cargo test --workspace` in CI** (incl. integration tests) —
  deferred: integration suites need a live Kubo daemon; lib scope matches the
  measured-green baseline and keeps the gate honest.

# References

- root PR #1613 (SDK deflake + stale-note cleanup + lockfile sync)
- kotoba PR #104 (coverage harness + baseline + pre_proxy fixture fix)
- kotoba PR #105 (CI workflow + host-triple override)
- kotoba `docs/ADR-ci-coverage.md` (engine-side record of 2–4)
- `20-actors/etzhayyim-sdk/src/kotoba-datomic/quorum.ts` (`collectQuorum`
  early-exit semantics)
- `40-engine/kotoba/crates/kotoba-auth/src/delegation.rs`
  (`MAX_CACAO_AGE_SECS = 7 days`)
