---
id: adr-2607011830-pqh-crypto-relocation-to-kotoba-lang
title: "ADR-2607011830: pqh crypto-agility seam relocation from etzhayyim-sdk to kotoba-lang/pqh"
status: accepted
doc_type: adr
topic: pqh-crypto-relocation
authoritative: true
last_verified: 2026-07-01
priority: 3.0
axis: architecture
weight: 0.30
priority_note: "Housekeeping/placement ADR, not a design change to the crypto-agility layer itself."
authoritative_for:
  - kotoba-lang/pqh repo location
  - etzhayyim-sdk's crypto/kdf/pq/did-signal/signal re-export shims
depends_on:
  - adr-2605181100-mst-encrypted-records-signal-keywrap
  - adr-2606111300-pq-hybrid-crypto-layer
related:
  - adr-2607011300-nv-compat-relocation-to-kotoba-lang
  - adr-2606302300
supersedes: []
superseded_by: []
---

# ADR-2607011830: pqh crypto-agility seam relocation from etzhayyim-sdk to kotoba-lang/pqh

**Status**: accepted
**Date**: 2026-07-01
**Deciders**: Jun Kawasaki

# Context

Following ADR-2607011300's relocation of `nv-compat`, a survey of what else
remains in `20-actors/etzhayyim-sdk/src/` found a second, cleanly-separable
generic substrate cluster: `crypto.ts` (XChaCha20-Poly1305 AEAD envelope),
`kdf.ts` (Argon2id KDF), `pq.ts` (post-quantum hybrid layer, suite
`pqh-v1` — X25519+ML-KEM-768, Ed25519+ML-DSA-65), `did-signal.ts`
(DID&harr;Signal `IdentityKey` binding verification), and `signal.ts` (a
deprecated toy in-memory session stand-in). None of these five files
reference any etzhayyim-specific NSID, Charter concept, or governance
logic as a compile-time constant — every collection name, DID, and purpose
value is a plain parameter. This is the same "any library/substrate belongs
in kotoba-lang" placement rule (ADR-2606302300) nv-compat and
`kami-engine`/`kami-engine-sdk` already executed.

Unlike `nv-compat`, this cluster has **real consumers**:

- `20-actors/etzhayyim-sdk/src/encrypted.ts` imports from `./crypto.js`,
  `./did-signal.js`, `./signal.js`, and `./pq.js` directly (it stays in
  `etzhayyim-sdk` — it is a thin, etzhayyim-namespaced orchestration layer
  over these primitives, not a generic primitive itself).
- `60-apps/etzhayyim-project-karute/appview/etzhayyim-wasm-karute-karu7t3e/
  svelte/src/lib/api/sdk-init.ts` imports `@etzhayyim/sdk/signal` (a
  type-only import today, but a real downstream dependency on the public
  package subpath).
- `70-tools/scripts/lint/substrate-boundary.mjs`'s hint text tells authors
  to use `@etzhayyim/sdk/crypto` / `@etzhayyim/sdk/signal` instead of
  importing `@noble/ciphers` / `@signalapp/libsignal-client` directly.

So this move cannot be a bare deletion the way nv-compat's was — the public
import surface `@etzhayyim/sdk/{crypto,kdf,pq,did-signal,signal}` must keep
resolving for existing consumers.

# Decision

Physically relocate the five files + their six dedicated test files
(`crypto.test.ts`, `kdf.test.ts`, `pq.test.ts`, `did-signal.test.ts`,
`did-doc-pq.test.ts`, `signal.test.ts` — the last two cover
`did-signal.ts`+`pq.ts` cross-module behavior and the `pq.ts`-into-
`signal.ts` session-wrap path respectively) **as-is** (TypeScript
unchanged) to a new repo, **`kotoba-lang/pqh`** — named after the code's own
suite identifier ("pqh-v1"), not `crypto`, because `kotoba-lang/crypto`
already exists as an unrelated, independently authored CLJC
foundational-stdlib repo (hash/HMAC/HKDF + a host-injected AEAD *interface*,
no cipher implementation — a lower abstraction layer than this package's
concrete AEAD/KDF/PQ-hybrid implementations). `test/encrypted-pq.test.ts`
stays in `etzhayyim-sdk` (it tests `encrypted.ts`, importing the relocated
modules only via the shim paths below).

`etzhayyim-sdk`'s own `src/{crypto,kdf,pq,did-signal,signal}.ts` become thin
re-export shims:

```typescript
export * from "@etzhayyim/pqh/crypto";
```

so every existing `@etzhayyim/sdk/*` import path — `encrypted.ts`'s relative
imports, the karute app's package-subpath import, and the lint rule's
guidance — keeps resolving unchanged. `@etzhayyim/pqh` is added to
`etzhayyim-sdk/package.json`'s `dependencies` as a git dependency
(`git+https://github.com/kotoba-lang/pqh.git#main`); no other file in
`etzhayyim-sdk` needed changes.

`kotoba-lang/pqh` is **public**, not private like this session's other new
repos — confirmed necessary, not just convenient: `etzhayyim/root`'s own
`sdk-test` CI job failed on the first push of this PR with `git+ssh://`
(`Permission denied (publickey)` — GitHub Actions runners carry no SSH key)
and would fail identically on `git+https://` against a *private* repo
(`GITHUB_TOKEN` is scoped to the workflow's own repo, not a cross-org
private clone). Public + `git+https://` needs no credential at all in any
environment. The package has no secrets or confidential logic — it is a
crypto-primitives wrapper — so this cost nothing beyond the default.

`kotoba-lang/pqh` **commits its `dist/` build output**, unlike
`kami-nv-compat` — a git-dependency install in an `allow-scripts`-gated
environment (confirmed empirically: `etzhayyim-sdk`'s own `npm install`
skips the `prepare` lifecycle script for this exact reason) never runs the
build step, so a consumer installing a git URL with no committed `dist/`
silently gets bare TypeScript source and every import resolves to nothing.
CI reinstalls with `--ignore-scripts` (mirroring real consumers) and diffs
`dist/` after a fresh `npm run build` to catch drift between `src/` and the
committed output.

# Consequences

- `kotoba-lang/pqh` becomes independently versioned and installable without
  pulling in `@etzhayyim/sdk`'s religious-corp-specific surface (BI/kisha,
  Charter compliance gate, donation-purpose enum, kotoba-datomic witness
  quorum) — a future non-etzhayyim actor needing the same AEAD/KDF/PQ-hybrid
  primitives can depend on it directly.
- `etzhayyim-sdk`'s public API is unchanged for every existing consumer;
  the cost is one extra `git+https://` dependency hop and a `dist/`-drift CI
  check that didn't previously need to exist for this code.
- As with ADR-2607011300, git history was not preserved (shallow monorepo
  clone) — this ADR plus ADR-2605181100/ADR-2606111300 are the durable
  record of *why* and *when*.
- This is a **physical move only**. A CLJC port (folding `crypto`/`kdf`
  onto `kotoba-lang/crypto`'s existing hash/HMAC/HKDF primitives where it
  makes sense, reimplementing the PQ hybrid and DID-Signal binding in
  `.cljc`) is deferred to a later, separate task — explicitly requested by
  the owner as sequencing ("物理移動を先に、cljc化は後で"), mirroring how
  `nv-compat` was relocated as-is before any Rust/CLJ backend-swap work.

# Alternatives Considered

## A1. Rename to `kotoba-lang/crypto` and let the existing repo absorb it

Rejected: the existing `kotoba-lang/crypto` is a different author's
independent, already-pushed CLJC work (foundational-stdlib hash/HMAC/HKDF +
an AEAD interface with no cipher). Merging a same-day TypeScript AEAD/KDF/
PQ-hybrid facade into that repo under the same name would conflate two
different abstraction layers and languages in one place. `pqh` keeps them
separate; a future CLJC port of this package can depend on
`kotoba-lang/crypto`'s primitives instead of duplicating them.

## A2. Delete the shims, rewrite `encrypted.ts` and the karute app to import `@etzhayyim/pqh` directly

Rejected for this move: it would touch a live downstream app
(`etzhayyim-project-karute`) and the lint rule's canonical guidance text as
part of what should be a placement-only refactor. Thin re-export shims
achieve the same end state (canonical implementation lives in
`kotoba-lang`) with zero blast radius on consumers; direct rewiring can
happen later if the shim layer itself is judged not worth keeping.

## A3. Keep `dist/` out of git and rely on the `prepare` npm lifecycle script

Tried first, rejected: this repo's own `npm install` (via `allow-scripts`)
skips `prepare` for the git dependency, leaving `node_modules/@etzhayyim/pqh`
with cloned source and no build output — every shim import failed to
resolve. Committing `dist/` (with a CI check that rebuilds and diffs it) is
the robust fix; keeping `prepare` too costs nothing for consumers that do
allow scripts.

# References

- ADR-2605181100 (MST encrypted records + Signal keywrap — design authority
  for crypto/signal/did-signal, unchanged by this move)
- ADR-2606111300 (PQ hybrid crypto layer — design authority for pq.ts,
  unchanged by this move)
- ADR-2606302300 (org-taxonomy 4-orgs — the library-placement rule this ADR
  executes)
- ADR-2607011300 (the nv-compat relocation this ADR follows the same pattern
  from, with the re-export-shim wrinkle this move additionally needed)
- `kotoba-lang/pqh` (new repo, `README.md` for provenance and the `dist/`
  commit rationale)
