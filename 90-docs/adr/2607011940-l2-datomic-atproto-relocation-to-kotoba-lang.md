---
id: adr-2607011940-l2-datomic-atproto-relocation-to-kotoba-lang
title: "ADR-2607011940: l2/paymaster, kotoba-datomic, atproto/pds relocation from etzhayyim-sdk to kotoba-lang"
status: accepted
doc_type: adr
topic: l2-datomic-atproto-relocation
authoritative: true
last_verified: 2026-07-01
priority: 3.0
axis: architecture
weight: 0.30
priority_note: "Housekeeping/placement ADR, not a design change to any of the three modules."
authoritative_for:
  - kotoba-lang/base-l2 repo location
  - kotoba-lang/witness-quorum repo location
  - kotoba-lang/atproto-client repo location
  - etzhayyim-sdk's remaining re-export shims (l2, paymaster, kotoba-datomic, atproto, pds)
depends_on:
  - adr-2605171800-langgraph-mst-ipfs-l2-anchor-pipeline
  - adr-2605231400-kotoba-datomic-holochain-iso-substrate
  - adr-2605172000
related:
  - adr-2607011300-nv-compat-relocation-to-kotoba-lang
  - adr-2607011830-pqh-crypto-relocation-to-kotoba-lang
  - adr-2607011930-ipfs-checkpointer-relocation-to-kotoba-lang
  - adr-2606302300
supersedes: []
superseded_by: []
---

# ADR-2607011940: l2/paymaster, kotoba-datomic, atproto/pds relocation from etzhayyim-sdk to kotoba-lang

**Status**: accepted
**Date**: 2026-07-01
**Deciders**: Jun Kawasaki

# Context

Completing the etzhayyim-sdk generic-substrate sweep begun in
ADR-2607011300 (nv-compat), ADR-2607011830 (pqh), and ADR-2607011930
(ipfs/checkpointer). Three remaining clusters were investigated and moved
in this pass:

1. **`l2.ts` + `paymaster.ts`** — Base L2 MST-root anchor client (viem) and
   a provider-agnostic ERC-4337 sponsored-write helper. Independent of
   each other's siblings; `pay.ts` (which imports `pds.ts`) was
   deliberately left in `etzhayyim-sdk` and out of this bundle.
2. **`kotoba-datomic/*`** (7 files: `attestation`, `orchestrator`,
   `pds-transport`, `quorum`, `signer`, `witness-selector`, `index`) —
   witness/quorum/attestation machinery. Before moving, investigated
   whether this was redundant with a Rust reimplementation
   ADR-2605262130 §D8 claimed existed: it does not. `kotoba-lang/kotoba`'s
   entire Rust workspace (including `kotoba-net`/`kotoba-dht`/
   `kotoba-server`, the crates ADR-2605262130 named as the successor) was
   deleted 2026-07-01 (PR #259) before ever reimplementing this domain,
   and the Python counterpart `signer.ts`'s docstring cites
   (`kotodama.kotoba-datomic`) is confirmed gone too. This TypeScript
   cluster was, at the time of relocation, the only complete working
   implementation of this logic anywhere in `kotoba-lang`.
3. **`atproto.ts` + `pds.ts`** — AT Protocol client facade + PDS
   read/write helpers over `@atproto/api`. Before moving, investigated
   whether `kotoba-lang/atproto` (an existing repo) already covered this:
   it does not — that repo is CLJC-only protocol vocabulary (`did?`,
   `repo-uri`/`parse-uri`, a static NSID→HTTP-method route table) with
   **zero HTTP/network code**, and its own roadmap marks `:client`/
   `:server` features `:planned`. Every function in `atproto.ts`/`pds.ts`
   is a genuine gap, not a duplicate.

# Decision

Physically relocate (TypeScript unchanged) to three new repos, matching
each cluster's actual scope:

- **`kotoba-lang/base-l2`**: `l2.ts` + `paymaster.ts`.
- **`kotoba-lang/witness-quorum`**: the 7 `kotoba-datomic/` files + their 3
  dedicated test files (renamed to drop the redundant `kotoba-datomic-`
  filename prefix: `signer.test.ts`, `pds-transport.test.ts`,
  `witnessed-write.test.ts`). Named `witness-quorum`, not `kotoba-datomic`
  — the directory's original name — to describe what the code actually
  does and avoid echoing the name of the now-deleted, unrelated Rust
  crate of the same name.
- **`kotoba-lang/atproto-client`**: `atproto.ts` + `pds.ts`. Named
  `atproto-client` (not `atproto` — already taken by the CLJC vocabulary
  repo) to make the distinction unambiguous.

All three are **public from creation** and commit their `dist/` build
output, matching `kotoba-lang/pqh`/`ipfs`/`checkpointer`.

`etzhayyim-sdk`'s own `src/{l2,paymaster,atproto,pds}.ts` and
`src/kotoba-datomic/index.ts` (the directory is kept, containing only the
one shim file, so `index.ts`'s existing relative import
`"./kotoba-datomic/index.js"` needs no change) become thin re-export
shims. Real consumers verified before this move: `atproto.ts`/`pds.ts` are
imported by `etzhayyim-project-hrse` (`AtpBaseClient` via
`@etzhayyim/sdk/atproto`) and `open-otology-uhl-r` (`getAgent`/
`createRecord` via `@etzhayyim/sdk/pds`) — both keep resolving unchanged
via the shim. `pay.ts` (staying in `etzhayyim-sdk`) imports `createRecord`/
`PdsConfig` from the now-shimmed `./pds.js` and needed **no changes at
all**. `l2.ts`/`paymaster.ts`/`kotoba-datomic` have no live code consumer
today (only doc/ADR/lint-hint references) — their shims exist to honor
the still-current public API contract those describe.

# Consequences

- All three new repos become independently versioned and installable
  without pulling in `@etzhayyim/sdk`'s religious-corp-specific surface.
- `etzhayyim-sdk`'s public API is unchanged for every real consumer
  checked (`etzhayyim-project-hrse`, `open-otology-uhl-r`, `pay.ts`).
- Three new `git+https://` dependency hops and `dist/`-drift CI checks.
- `kotoba-datomic/*` had dedicated tests (35 assertions across 3 files)
  that moved with it and pass unchanged in the new repo; `l2`/`paymaster`/
  `atproto`/`pds` had none to bring along (a pre-existing gap).
- `etzhayyim-sdk`'s own test suite: 53 tests / 7 files passing after this
  move (down from 88/10 — the 35 tests / 3 files that moved to
  `witness-quorum`), typecheck and build both clean.
- Physical move only — a CLJC port remains deferred to a later, separate
  task for all three, same as the prior relocations in this sweep.

This completes the etzhayyim-sdk generic-substrate sweep begun with
`nv-compat`. What remains in `etzhayyim-sdk` after this ADR
(`index.ts`, `abi.ts`, `bi.ts`, `charter-compliance-gate.ts`, `donate.ts`,
`encrypted.ts`, `pay.ts`) is etzhayyim-specific religious-corp business/
governance logic that was explicitly classified as staying, per the
survey this whole sweep started from.

# References

- ADR-2605171800 (LangGraph MST/IPFS/L2-anchor pipeline — design authority
  for `l2.ts`)
- ADR-2605172100 "Gas sponsorship" (design authority for `paymaster.ts`)
- ADR-2605231400 / ADR-2605262130 (kotoba-datomic composition spec +
  its claimed-but-unrealized Rust successor)
- ADR-2605172000 (substrate-boundary rules — design authority for
  `atproto.ts`/`pds.ts`)
- ADR-2606302300 (org-taxonomy 4-orgs — the library-placement rule this
  ADR executes)
- ADR-2607011300 / ADR-2607011830 / ADR-2607011930 (the prior relocations
  in this sweep)
- `kotoba-lang/base-l2`, `kotoba-lang/witness-quorum`,
  `kotoba-lang/atproto-client` (new repos, `README.md` for provenance)
