---
id: adr-2606041657-session-close-kotoba-durability-and-canonical-tier
title: "ADR-2606041657: Session close — kotoba durability (B2 cold pin) + canonical-tier hardening (CommitDag-as-WAL + incremental MV)"
status: active
doc_type: adr
topic: session-close-kotoba-durability-and-canonical-tier
authoritative: false
last_verified: 2026-06-04
priority: 5.0
axis: architecture
weight: 0.40
priority_note: "Documentation-only closure; authoritative designs = ADR-2606041130 + 2606041151"
authoritative_for: []
depends_on:
  - "2606041130"
  - "2606041151"
related:
  - "2605262130"
  - "2605312345"
  - "2606012100"
supersedes: []
superseded_by: []
---

# ADR-2606041657: Session close — kotoba durability + canonical-tier hardening

**Status**: active
**Date**: 2026-06-04
**Deciders**: Jun Kawasaki

# Context

Documentation-only closure for the 2026-06-03→04 session that started from
*「今の kotoba server は安定して write/read/永続化できているか」* and progressed
through durability, structural analysis, and a first-tier-query implementation.
Authoritative designs: **ADR-2606041130** (B2 cold pin) + **ADR-2606041151**
(CommitDag-as-WAL + incremental MaterializedView).

# Decision

(Documentation only — no new decision; records what was empirically found, fixed,
designed, built, and shipped.)

## 1. Stability + durability triage (live server)

- The live kotoba server (`:8077`, launchd `com.etzhayyim.kotoba`) was found
  failing its durable commit (`kotoba commit` 30 s hang → 500) due to **version
  skew** — the running binary was 68 commits behind `main`. Rebuilt from source
  with capability parity (`--features wasm-runtime`), ad-hoc re-signed, restarted;
  `commit` rc=0, write→read E2E green.
- **IPFS was on the full internal disk** (`~/.ipfs`, durable cold-puts failing
  `no space`). Migrated the live kubo repo (identity-preserving) to the
  926 GB-free external volume (`/Volumes/260317/etzhayyim/ipfs-repo`) and made it
  **launchd-managed** (`com.etzhayyim.ipfs`, IPFS_PATH + HOME), StorageMax 10→200 GB.

## 2. Off-host durability — B2 cold pin (ADR-2606041130)

`50-infra/kotoba-b2-pin/` — DataLad + git-annex S3 special remote mirroring **every
local kubo block** (`ipfs refs local`, multihash-keyed → complete; head-DAG export
is only ~5 KB, so the block store itself is the durable unit) to Backblaze B2;
incremental + drop-after-copy; restore via `ipfs block put`. Creds from 1Password
at runtime (`embedcreds=no`, no-server-key). **Full backfill complete: 26,634 /
26,634 blocks on B2.** Verified loss-recovery (block rm → restore → 957 B).

## 3. Structural analysis (ADR-2606041151)

Source-grounded findings: the in-memory Arrangement + Journal WAL are *not
structurally necessary* (authors' own note: *"in-memory Arrangement is only an
optimisation"*; the Journal is a per-assert 4-topic double-write); the Datomic
*data model* is tier-1 but the Datalog *query engine* re-evaluated from scratch
per request (`MaterializedView` IVM existed but was unwired). Answered
*「local IPFS を持てば同期コミット不要か」*: WAL-necessity ⟂ IPFS locality — it
comes from deferring commits; the CommitDag already **is** the WAL.

## 4. Shipped upstream — etzhayyim/kotoba `main` (PRs #26–#32)

| PR | Change |
|---|---|
| #26 | architecture SVG redraw + README prune (CommitDag-as-WAL, kotoba-as-own-pinner) + analysis SVG |
| #27 | `FsBlockStore` — embedded durable content-addressed block store |
| #28 | server `TieredBlockStore<Memory, FsBlockStore>` wiring (A) + `MvRegistry` primitive (B) |
| #29 | `mv_registry` in state + maintain-on-commit + `kg.mv.register` / `kg.mv.result` (B) |
| #30 | `KOTOBA_JOURNAL_WAL=off` opt-out — drop the redundant WAL double-write (A) |
| #31 | crash-recovery test — recover from the CommitDag alone, no journal (A) |
| #32 | `kg.query` `mv_name` routing — serve a maintained MaterializedView (B) |

# Consequences

**Decision A (CommitDag-as-WAL): functionally complete + recovery-validated.**
A.1 embedded store ✅ · A.2 micro-batch synchronous commit = **already present**
(DistributedCommitWriter per ingest) ✅ · A.3 Journal WAL opt-out ✅ · A.4 recovery
validated ✅ · A.5 restart-from-CommitDag = **already present** (`replay_from_journal`
restores the CommitDag from the checkpoint, written by `commit()` independent of the
per-datom WAL; entry-replay is an empty no-op when WAL is off) ✅. **A.6 open**: the
default flip to WAL-off is *not yet free* — cold reads don't promote to the hot
arrangement, so a WAL-off restart keeps reads on the cold path until rewrites;
prerequisite = a boot-time legacy-arrangement rehydration from the CommitDag.
**WAL-off stays opt-in.**

**Decision B (incremental MaterializedView): server-wired.** Register a SPARQL/
Cypher view, maintained on every commit, read via `kg.mv.result` or `kg.query`
`mv_name`. Follow-on: auto-match an arbitrary query to an equivalent view.

ZERO Charter invariant amendments across the session (Datom log canonical, no
server key — pinning is content-addressed, Murakumo-only inference untouched).

# Alternatives Considered

(See the authoritative ADRs — 2606041130 §Alternatives, 2606041151 §Alternatives.)
This close did not rush the durability-core default flip (A.6) nor a full Journal
code removal; both are deliberately staged.

# References

- 90-docs/adr/2606041130-kotoba-b2-blockstore-cold-pin.md (authoritative — B2 pin)
- 90-docs/adr/2606041151-kotoba-commitdag-as-wal-and-incremental-query-tier.md (authoritative — A/B)
- 50-infra/kotoba-b2-pin/README.md
- 40-engine/kotoba/docs/kotoba-datomic-architecture.svg + kotoba-canonical-vs-optimization.svg
- etzhayyim/kotoba PRs #26–#32 (merged to `main`)

# Durability of this record (concurrent rebase note)

This monorepo branch is being force-push-rebased by the in-progress
rename-cutover (cf. ADR-2606032330's note: *"surviving untracked files must be
committed/stashed before next rebase"*). That rebase periodically resets tracked
files (`deps.toml`, `90-docs/adr/README.md`) to a pre-cutover state, dropping
hand-added registry rows — which is why this session's earlier `deps.toml` /
adr-README registrations were lost and re-applied here.

**Durable artifacts of this session (rebase-safe):**
- The ADR `.md` files (new files survive the rebase): 2606041130, 2606041151,
  this 2606041657.
- **All engine work is on GitHub**, immune to the monorepo rebase:
  `etzhayyim/kotoba` `main` (PRs #26–#32 merged) + the `50-infra/kotoba-b2-pin`
  tooling.

If the `deps.toml` / adr-README rows for 2606041130 / 2606041151 / 2606041657 are
missing after the next rebase, re-apply them from this ADR's reference list.
