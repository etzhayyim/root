---
id: adr-2607011930-ipfs-checkpointer-relocation-to-kotoba-lang
title: "ADR-2607011930: ipfs + checkpointer relocation from etzhayyim-sdk to kotoba-lang/{ipfs,checkpointer}"
status: accepted
doc_type: adr
topic: ipfs-checkpointer-relocation
authoritative: true
last_verified: 2026-07-01
priority: 3.0
axis: architecture
weight: 0.30
priority_note: "Housekeeping/placement ADR, not a design change to either module."
authoritative_for:
  - kotoba-lang/ipfs repo location
  - kotoba-lang/checkpointer repo location
  - etzhayyim-sdk's ipfs/checkpointer/checkpointer-bin re-export shims
depends_on:
  - adr-2605171800-langgraph-mst-ipfs-l2-anchor-pipeline
related:
  - adr-2607011300-nv-compat-relocation-to-kotoba-lang
  - adr-2607011830-pqh-crypto-relocation-to-kotoba-lang
  - adr-2606302300
supersedes: []
superseded_by: []
---

# ADR-2607011930: ipfs + checkpointer relocation from etzhayyim-sdk to kotoba-lang/{ipfs,checkpointer}

**Status**: accepted
**Date**: 2026-07-01
**Deciders**: Jun Kawasaki

# Context

Continuing the etzhayyim-sdk generic-substrate sweep (ADR-2607011300,
ADR-2607011830), `src/checkpointer.ts` — the LangGraph `MstCheckpointSaver`
wire-protocol sidecar (ADR-2605171800 Stages 1-2) — was the next clean
candidate. It has no etzhayyim-specific coupling beyond two overridable
default config values (`socketPath: "/run/etzhayyim/checkpointer.sock"`,
`stateDir: ~/.etzhayyim/checkpointer`).

It is not, however, self-contained the way the `pqh` cluster was: it
imports `pinBlob` from `./ipfs.js` (etzhayyim-sdk's Kubo HTTP client
wrapper) and `decrypt`/`encrypt`/`generateKey`/`KEY_BYTES`/`SymmetricKey`
from `./crypto.js` (already a re-export shim over `kotoba-lang/pqh`, per
ADR-2607011830). `ipfs.ts` itself is used by a second consumer,
`index.ts`'s `Etzhayyim` class (`ipfsModule.pinBlob`/`fetchBlob` for its own
blob read/write methods, plus `export * as ipfs from "./ipfs.js"`) — so
`ipfs.ts` has to move (or stay) as its own decision, independent of
`checkpointer.ts`.

A repo-wide grep found no live code anywhere importing
`@etzhayyim/sdk/checkpointer` or `@etzhayyim/sdk/ipfs` today — only
doc/ADR/comment references describing a *future* migration (`ameno`'s
daemon, `substrate-boundary.mjs`'s lint hints). Unlike the `pqh` move,
there is no live external consumer to keep working; the shims exist to
honor the still-current public API contract those docs describe, not to
avoid breaking something today.

# Decision

Physically relocate (TypeScript unchanged) to two separate new repos,
matching each module's actual scope rather than bundling them:

- **`kotoba-lang/ipfs`**: `src/ipfs.ts` alone. Trivial (102 lines, zero npm
  dependencies — only global `fetch`/`Blob`/`FormData`), and a genuinely
  separate, independently reusable concern from the checkpoint sidecar.
- **`kotoba-lang/checkpointer`**: `src/checkpointer.ts` +
  `src/checkpointer-bin.ts`. Depends on `@etzhayyim/ipfs` (replacing
  `./ipfs.js`) and `@etzhayyim/pqh/crypto` (replacing `./crypto.js`) as
  ordinary npm dependencies instead of local relative imports.

Both repos are **public** from creation (not private-then-fixed, learning
from `pqh`'s CI incident) — neither carries secrets or confidential logic,
and a private repo would break any CI (in `etzhayyim/root` or elsewhere)
that installs it as a git dependency, since GitHub Actions runners have no
SSH key and `GITHUB_TOKEN` cannot authenticate a cross-org private clone.
Both use `git+https://` dependency URLs and commit their `dist/` build
output for the same `allow-scripts`-gated-environment reason as
`kotoba-lang/pqh` (see its README).

`etzhayyim-sdk`'s own `src/ipfs.ts` and `src/checkpointer.ts` become thin
re-export shims (`export * from "@etzhayyim/ipfs"` /
`"@etzhayyim/checkpointer"`), preserving `index.ts`'s existing relative
import and the public `@etzhayyim/sdk/{ipfs,checkpointer}` subpaths.
`src/checkpointer-bin.ts` needs a **side-effect import**
(`import "@etzhayyim/checkpointer/checkpointer-bin";`), not `export *` —
the original module runs `main()` at top level and exports nothing, so a
re-export would silently do nothing; verified by actually running the
compiled shim (`node dist/checkpointer-bin.js`), which executed all the
way into the relocated package's real `runFromEnv()`/`main()` and failed
on a legitimate missing-env-var configuration error, not an
import-resolution error.

# Consequences

- `kotoba-lang/ipfs` and `kotoba-lang/checkpointer` become independently
  versioned and installable; any future non-etzhayyim actor needing a Kubo
  client or a LangGraph MST-checkpoint sidecar can depend on them directly
  without pulling in `@etzhayyim/sdk`'s religious-corp-specific surface.
- `etzhayyim-sdk`'s public API is unchanged; the doc-described future
  consumers (`ameno`'s daemon, the lint rule's guidance) still resolve
  `@etzhayyim/sdk/checkpointer` and `@etzhayyim/sdk/ipfs` to real code.
- Two new `git+https://` dependency hops and `dist/`-drift CI checks
  (mirroring `pqh`'s) didn't previously need to exist for this code.
- Neither module had dedicated tests in `etzhayyim-sdk` to bring along
  (a pre-existing gap, not introduced by this move).
- Physical move only — a CLJC port remains deferred to a later, separate
  task, same as `nv-compat` and `pqh`.

# Alternatives Considered

## A1. Bundle ipfs.ts into the checkpointer repo instead of a separate repo

Rejected: `ipfs.ts` is a small, independently reusable Kubo client with no
inherent relationship to LangGraph/MST/CAR beyond being one of
`checkpointer.ts`'s two dependencies. `index.ts` also depends on it
directly, unrelated to checkpointing. Keeping it a separate repo (matching
the one-concern-one-repo pattern `nv-compat`/`pqh` already established)
lets it be depended on alone.

## A2. Start both repos private, fix visibility only if CI breaks

Rejected on the strength of the `pqh` precedent: the failure mode (GitHub
Actions has no SSH key; `GITHUB_TOKEN` can't clone a private cross-org repo
over HTTPS either) is now known in advance, not a surprise to debug again.
Public from creation costs nothing for code with no secrets.

# References

- ADR-2605171800 (LangGraph MST/IPFS/L2-anchor pipeline — design authority
  for checkpointer.ts, unchanged by this move)
- ADR-2606302300 (org-taxonomy 4-orgs — the library-placement rule this ADR
  executes)
- ADR-2607011300 / ADR-2607011830 (the nv-compat and pqh relocations this
  ADR follows the same pattern from)
- `kotoba-lang/ipfs`, `kotoba-lang/checkpointer` (new repos, `README.md` for
  provenance)
