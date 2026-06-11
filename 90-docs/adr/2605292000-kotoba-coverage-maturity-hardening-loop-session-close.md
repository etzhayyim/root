---
id: adr-2605292000-kotoba-coverage-maturity-hardening-loop-session-close
title: "ADR-2605292000: kotoba coverage + maturity hardening — /loop session closure (2026-05-29, 17 iterations)"
status: accepted
doc_type: adr
topic: kotoba-coverage-maturity-hardening
authoritative: true
last_verified: 2026-05-29
priority: 5.0
axis: closure
weight: 0.30
priority_note: "Session-closure ADR for a 17-iteration /loop coverage+maturity hardening sprint on the kotoba workspace (network層 first, local-runnable scope). Pure quality work: +37 tests/doctests, ~72 clippy issues cleared, 4 build-breaking clippy errors fixed, 1 spurious test failure fixed → clean `cargo test --workspace` (1846/0). No constitutional decisions; navigation + record only."
authoritative_for:
  - record of the 2026-05-29 kotoba test-coverage + clippy-maturity hardening pass
  - kotoba workspace green-test baseline (1846 passed / 0 failed / 12 ignored) as of 2026-05-29
depends_on:
  - adr-2605291100-manimani-kotoba-native-reconciliation-gmail-pc-ingest
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
related:
  - adr-2605290900-kotoba-monorepo-projection-r0-r1-session-close
supersedes: []
superseded_by: []
---

# ADR-2605292000: kotoba coverage + maturity hardening — /loop session closure

**Status**: accepted
**Date**: 2026-05-29
**Deciders**: Jun Kawasaki

# Context

This session began with ADR-2605291100 (manimani reconciled onto kotoba EAVT + StateGraph
+ Murakumo + Signal E2E), then the operator issued a `/loop` directive:

> 「coverage と成熟度を高めて。まずこの端末、network から初めて.」
> (Continuously raise test coverage + code maturity; start from this terminal / the network
> layer; each iteration: measure → pick the single weakest spot → improve → verify → report.)

The loop ran as a 30-minute session cron (`*/30 * * * *`) for **17 iterations**, all executed
locally against the `40-engine/kotoba/` Rust workspace (the network/storage/runtime spine that
the manimani ingest design depends on). This ADR records the outcome and closes the loop.

No constitutional decisions were made. This is a quality / navigation record (axis = closure,
weight 0.30 so it sorts below substantive ADRs).

# Decision

Record the session's verified end-state as the kotoba quality baseline and stop the loop
(cron `6df6f27d` cancelled). Per-iteration the loop chose the single highest-value weakest
spot, made one focused change, and verified it before reporting.

## What landed (29 files across 13 crates, all local-verified)

**New test coverage (+34 unit tests, +3 doctests):**
- `kotoba-net/behaviour.rs`: +2 — construction + `KotobaBehaviourEvent` variant-exhaustiveness guard for the combined libp2p NetworkBehaviour (was 0 tests).
- `kotoba-ingest/gmail.rs`: +8 — Gmail wire-contract serde (`threadId`/`historyId`/`messagesAdded` mapping, empty-delta cases) + base64url (`URL_SAFE_NO_PAD`) decode guards (was 0).
- `kotoba-ipfs` (`store.rs`+`node.rs`): +15 — `cid_for` CIDv1/RAW/SHA2-256 correctness, `MemBlockStore` content-addressing/idempotency/Arc-share, async `IpfsCodec` CBOR round-trips; `PartialEq`/`Eq` added to the `BlockRequest`/`BlockResponse` wire enums (crate was 0 tests → 15).
- `kotoba-runtime/executor.rs`: +6 — gas-less-execution prohibition (`new(0)` errors), `SerializedQuad: From<PendingQuad>`, ChainEntry CBOR round-trips (was 0).
- `kotoba-llm/http_infer.rs`: +3 — extracted `build_chat_request_body` / `parse_chat_response` pure fns from the async OpenAI-compatible (Murakumo/LiteLLM) path; tests lock the `/v1/chat/completions` shape (`stream:false`) + error-on-missing-content (feature `http-inference`).
- 3 `ignore`d doc examples (`kotoba-vm` StateGraph builder, StateSchema, `Tool::from_fn`) converted to **compiled + runnable** doctests against the live API.

**Maturity / clippy (~72 issues cleared; 4 build-breaking errors fixed):**
- Fixed 4 deny-by-default `clippy::approx_constant` **errors** that broke the clippy test-build of `kotoba-server` (`kg.rs`, 2) and `kotoba-kqe` (`quad.rs`, 2) — arbitrary `3.14`/`2.718…` test floats misread as PI/E → neutral values.
- Fixed a **spurious failing test**: `kotoba-runtime::tests::test_wasm_instantiate` hard-read an unbuilt `kotoba_hello.wasm` fixture (failed on any clean checkout) → `#[ignore]` with reason + run instructions. `cargo test --workspace` is now green by default.
- Brought to a **zero-warning clippy baseline**: `kotoba-net`, `kotoba-ipfs`, `kotoba-ingest`, `kotoba-kqe`, `kotoba-graph`, `kotoba-auth`, `kotoba-signal`, `kotoba-store`, `kotoba-kse`, `kotoba-dht`, `kotoba-runtime`. Remaining: `kotoba-server` 2 cosmetic `items_after_test_module` (deferred — relocating large test modules is high-risk for a cosmetic lint).
- Two production helpers extracted with real tests (de-dup + testability): `nprobe_exceeds_limit` (cc_xrpc, both search/RAG handlers) and `clamp_kg_result_limit` (kg handler).
- 16+ const-bound `assert!` guards upgraded to compile-time `const _: () = assert!(...)` (server + kqe + signal) — a violated invariant now fails to compile, not at test-time.
- Mechanical lints cleared via `cargo clippy --fix` (MachineApplicable only, always re-verified): needless borrows, arg-less `format!`, `is_some_and`/`matches!`, non-NFKC `µ` identifiers, type-complexity alias, etc.

## Verified end-state

- `cargo test --workspace --no-fail-fast` → **1846 passed, 0 failed, 12 ignored** (the 12 = fixture/doc-gated; clean checkout is green).
- `cargo clippy --all-targets` → zero warnings across all kotoba crates except `kotoba-server` (2 cosmetic).

# Consequences

**Positive**: clean `cargo test`/`cargo clippy` baseline for the kotoba spine; the network,
IPFS, Gmail-ingest, runtime gas-guard, and Murakumo HTTP-inference wire contracts are now
test-covered; manimani-critical StateGraph/agent doc examples are rot-protected.

**Negative / open**: no CI gate yet locks this baseline in (repo "Future Work" still lists
GitHub Actions / lefthook clippy hooks as pending) — without a gate it can regress. The kotoba
changes live in the `40-engine/kotoba/` git subrepo and are uncommitted here; committing /
subrepo-push is a follow-up.

# Follow-ups

1. Commit the 29 kotoba working-tree changes + git-subrepo push to `github.com/etzhayyim/kotoba`.
2. Lock the baseline: lefthook pre-commit `cargo clippy -- -D warnings` + `cargo test` for kotoba (repo Future Work).
3. `kotoba-server` 2 `items_after_test_module` (relocate `lib.rs` / `email_xrpc.rs` test modules to EOF).
4. Remaining 9 `ignore`d doc examples (`kotoba-vm` module-level `//!` blocks) need real setup objects to become runnable.
5. manimani Phase 1+ (ADR-2605291100): implement the EAVT predicate module + StateGraph; then Gmail full-archive + PC-file ingest.

# Alternatives Considered

- **Chase the 2 cosmetic server warnings to absolute zero** — rejected this session: relocating
  multi-hundred-line test modules is high edit-risk for a style lint with no correctness value.
- **`cargo clippy --fix` blindly across the workspace** — rejected as the *primary* method;
  used only for MachineApplicable lints and always re-verified with `cargo test`, because
  autofix on security-sensitive crates (auth/signal) warrants a behavior check.

# References

- ADR-2605291100 (manimani kotoba-native reconciliation — the session's starting point + Phase-1 dependency)
- ADR-2605262130 (kotoba storage substrate unification)
- ADR-2605215000 (Murakumo-only inference — the `http_infer.rs` path under test)
- ADR-2605290900 (prior kotoba session-closure ADR — sibling closure pattern)
