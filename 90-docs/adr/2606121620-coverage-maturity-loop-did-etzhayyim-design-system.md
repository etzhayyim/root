---
id: adr-2606121620-coverage-maturity-loop-did-etzhayyim-design-system
title: "ADR-2606121620: Coverage/maturity loop wave — did:etzhayyim codec+CID suite + design-system motion + genesis-test fix"
status: accepted
doc_type: adr
topic: coverage-maturity-loop
authoritative: true
last_verified: 2026-06-12
priority: 4.0
axis: architecture
weight: 0.40
priority_note: "Verification-layer maturity; no runtime/invariant change."
authoritative_for:
  - did:etzhayyim codec + CID test coverage status
  - design-system motion utility test coverage status
depends_on: []
related:
  - 2606111640
  - 2605241800
supersedes: []
superseded_by: []
---

# ADR-2606121620: Coverage/maturity loop wave — did:etzhayyim codec+CID suite + design-system motion + genesis-test fix

**Status**: accepted
**Date**: 2026-06-12
**Deciders**: Jun Kawasaki

# Context

The recurring `/loop` cron (`8bd992ca`, every 30 min, prompt "coverage, matulity を向上")
runs one self-contained verification-hardening iteration per firing: find a high-value
zero-test pure-logic module, add comprehensive tests against known vectors, open a PR,
merge on green CI, clean up the worktree. This ADR records the 2026-06-11→12 continuation
of that loop (iterations 22–25), which converged on the **`did:etzhayyim` DID-method core**
(`10-protocol/did-etzhayyim/`) plus one design-system target — a direct continuation of the
portfolio-QA maturity wave (ADR-2606111640).

The `did:etzhayyim` content-addressing stack (ADR-2605241800 / ADR-0029) is foundational:
a genesis-op CID is `multibase(base32)` over a `multihash` over the **canonical DAG-CBOR**
of the op. Before this wave the entire codec→multihash→CID chain had only an indirect smoke
test via `genesis.test.ts`, which *itself carried a self-contradictory, always-failing
assertion* (asserting the CID started with both `bafy` and `bafkrei`).

# Decision

Land four scoped PRs off `origin/main`, each in an isolated worktree, merged on green CI:

1. **#1673 — design-system motion utilities** (`40-engine/svelte/design-system/.../motion/index.ts`).
   13 tests over pure transform/easing math (stagger delay clamping, overshoot/elastic easing
   boundaries, `computeTilt` 3D-transform math, `parallaxY`, slide/depth/spring param builders,
   spring-preset constants). Test-island pattern (own `package.json` outside the pnpm-workspace
   glob) keeps root `pnpm-lock.yaml` untouched; module is import-safe (svelte dependency is an
   erased `import type`).

2. **#1674 — did:etzhayyim codecs** (`cbor.ts` / `multibase.ts` / `multihash.ts`).
   26 tests: DAG-CBOR integer-width minimality + canonical map-key ordering + float rejection;
   base32/base16 round-trips and base58btc against the RFC-4648 (`'f'→'my'`) and Bitcoin
   (`'Hello World!'→'2NEpo7TZRRrLZSi2U'`) known vectors; multihash varint framing incl. a
   `>127` digest length forcing a multi-byte varint.

3. **#1676 — genesis-test correctness fix** (`test/genesis.test.ts`).
   Corrected the contradictory root-DID assertion: `genesis.ts` builds the CID with the **raw**
   multicodec (`0x55`), so the prefix is `bafkrei…`, not `bafy…` (dag-cbor `0x71`). Test-only
   change; brought a previously-red module green.

4. **#1677 — CIDv1 assembler + parsers** (`cid.ts`).
   14 tests: multicodec table; `createCidV1` exact byte layout `0x01 0x55 0x12 0x20 …` and the
   canonical IPFS vector `bafkreibm6jg3ux5qumhcn2b3flc3tyu6dmlb4xa7u5bf44yegnrjhc4yeq` for
   `"hello"`; the `json` codec (`0x0200`) emitting a multi-byte codec varint; `cidv1FromString`/
   `FromBytes` round-trips across raw/dag-cbor/json plus all three parser error paths; and
   `verifyCidV1` accept/reject on tampered content and codec mismatch.

**Outcome**: the `did:etzhayyim` package suite went from 8 partial (1 failing) to **48/48 green**
(8 genesis + 26 codec + 14 cid).

# Consequences

- The DID-method content-addressing chain is now pinned against canonical IPFS/RFC/Bitcoin
  vectors — a regression in key ordering, integer minimality, base32 bit-packing, varint
  framing, or CID version/codec framing now fails a test instead of silently changing every CID.
- **Honest boundary**: CI does **not** run the `did-etzhayyim` package's vitest (the package sits
  outside the pnpm-workspace glob; no path-scoped job in `.github/workflows/test.yml`). These
  suites are durable and runnable via `pnpm -F @etzhayyim/did-etzhayyim test` but are not yet
  CI-exercised. Adding a path-scoped job is a recommended follow-up (now unblocked — the suite
  is fully green, so a new job would land green).
- No source/runtime behavior changed except the test-only genesis fix. **ZERO invariant
  amendments** (no Charter/Rider/substrate-boundary impact).

# Alternatives Considered

- **Add a CI job for did-etzhayyim in the same wave** — deferred. It would have required fixing
  the genesis failure first (done in #1676) and is cleaner as its own follow-up PR.
- **One mega-PR** — rejected; per-module PRs keep each diff reviewable and each worktree
  independently mergeable, consistent with the loop's established pattern.

# References

- ADR-2606111640 — Portfolio QA wave (the maturity audit this continues)
- ADR-2605241800 — agentURI / did:etzhayyim 5-layer
- PRs #1673, #1674, #1676, #1677
- `10-protocol/did-etzhayyim/test/{genesis,codec,cid}.test.ts`
