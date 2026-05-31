---
id: adr-2605312355-session-close-kotoba-datom-first-class-and-charter-rider-d1
title: "ADR-2605312355: Session close — kotoba Datom first-class state + SHA2-256 CID + Charter Rider D1 applied"
status: active
doc_type: adr
topic: session-close
authoritative: true
last_verified: 2026-05-31
priority: 3.0
axis: closure
weight: 0.30
priority_note: "Documentation-only closure for the 2026-05-31 session that (1) made the kotoba Datom log the first-class canonical state (ADR-2605312345), (2) merged kotoba upstream main into the submodule confirming the single SHA2-256 CID unification + landing multimodal cross-modal search, (3) corrected a stale subrepo escape-symlink audit baseline after the kotoba git-subrepo → git-submodule migration, and (4) applied the Charter Compliance Rider v2.0 to kotoba upstream (ADR-2605262130 Phase-1 deliverable D1). Verification record + PR/commit provenance + one incident post-mortem (empty-tree commit caught pre-merge)."
authoritative_for:
  - "session provenance 2026-05-31 (kotoba Datom / SHA2-256 / Charter Rider D1)"
  - "ADR-2605262130 D1 completion record (Charter Rider applied to kotoba upstream)"
depends_on:
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605262130-kotoba-storage-substrate-unification
related:
  - adr-2605302200-kotoba-multimodal-cross-modal-search
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
supersedes: []
superseded_by: []
---

# ADR-2605312355: Session close — kotoba Datom first-class state + SHA2-256 CID + Charter Rider D1

**Status**: active
**Date**: 2026-05-31
**Deciders**: Jun Kawasaki

# Context

A 2026-05-31 session started from two founder questions — "do the ADRs still
carry IPFS/MST, and can kotoba's datomic be made first-class?" and "kotoba's CID
was unified to SHA2-256, hadn't it?" — and ran through to applying the Charter
Compliance Rider to the kotoba upstream repo. This ADR is a documentation-only
closure recording what landed, with PR/commit provenance and one incident
post-mortem.

# Decision

Closure record. No new constitutional decision; the substantive doctrine change
(Datom first-class) is ADR-2605312345 and the Charter Rider obligation is
ADR-2605262130 D1 (now satisfied).

## What landed (in order)

1. **ADR-2605312345 — kotoba Datom log = first-class canonical state.**
   Reframed the substrate-boundary State row: the kotoba Datom log
   (content-addressed EAVT Datalog, Datomic-isomorphic) is the canonical state
   primitive; IPFS = block backend, AT Proto MST = ingress/interop wire, Base L2
   = trust anchor. Resolved the contradiction between kotoba's README ("the
   distributed Datom DB is the source of truth") and the old doctrine that
   listed MST+IPFS+L2 as State with the Datom as a regenerable cache. No
   constitutional invariant changed. (`CLAUDE.md` State/engine/read-path rows +
   `deps.toml` `state_canonical` + ADR README.)

2. **kotoba submodule merged upstream main — single SHA2-256 CID confirmed.**
   The submodule was on a feature branch 51 commits behind kotoba main. Merged
   `origin/main` (preserving un-upstreamed multimodal work first), resolving 3
   conflicts (`CLAUDE.md` union, `deps.toml` both ADRs, `mcp.rs` took main's
   content-addressed `program_cid` OOM fix). **Empirically confirmed the CID is
   unified to a single SHA2-256 CIDv1** (`kotoba-core/src/cid.rs` uses
   `Sha256::digest`; dual-CID/blake3 index removed in kotoba `144df21`,
   2026-05-27). The earlier "dual-CID" description was a stale pre-merge doc;
   corrected stale `Dual-CID` wording in kotoba `CLAUDE.md` + store doc-comments.
   `cargo check --workspace` green. **kotoba PR #10** (multimodal MediaIngestor /
   cross-modal search ADR-2605302200 + LangGraph/WASM-runtime fixes + CID doc
   correction) merged to kotoba main.

3. **root PR #301** (feat/social-security-for-humanity → main) merged — landed
   ADR-2605312345 + the kotoba submodule bump (`918e8a7`) + the rest of the
   feature branch.

4. **Audit baseline correction (root PR #302).** The `audit-health`
   `subrepo-symlink-health` baseline expected 18 escape symlinks — entirely the
   kotoba git-subrepo's `CHARTER-RIDER.md → ../../CHARTER-RIDER.md` pattern (1
   root + 17 crates), a root-side artifact the audit itself flags as a defect.
   kotoba had migrated git-subrepo → git-submodule, so the scan correctly finds
   0. Re-baselined `EXPECTED_ESCAPE_SYMLINKS` 18 → 0 and rewrote the two coupled
   tests to assert the resolved end-state (not a regression). `test_subrepo_scripts.py`
   16/16 pass.

5. **Charter Rider D1 applied to kotoba upstream (kotoba PR #11 + root PR #304).**
   The audit finding surfaced that kotoba upstream shipped `license = "Apache-2.0"`
   only — Charter Rider v2.0 (ADR-2605262130 D1) was unmet. Applied directly in
   the kotoba repo (N5: no forking, upstream-PR only): added a **real**
   `CHARTER-RIDER.md` (canonical 239-line copy — *not* a `../../` escape symlink,
   which would dangle on standalone clone — the very defect retired by the
   submodule migration), a `NOTICE` reference block, and a README license note.
   Workspace-level NOTICE + CHARTER-RIDER.md covers all member crates via
   `license.workspace = true` (cf. `50-infra/yata`). root submodule bumped
   `918e8a7 → ecba123d`. **ADR-2605262130 D1 is now satisfied.**

## Provenance

| Artifact | Ref |
|---|---|
| Datom-first-class ADR | ADR-2605312345 |
| kotoba multimodal + merge + CID doc | kotoba PR #10 → kotoba `918e8a7` |
| root feature-branch merge | root PR #301 → main `f85a46d4a` |
| audit escape-symlink re-baseline | root PR #302 → main `d1003ae6f` |
| Charter Rider v2.0 on kotoba | kotoba PR #11 → kotoba `ecba123d` |
| root submodule bump (Rider) | root PR #304 |

# Consequences

- ADR-2605262130 **D1 = DONE** (Charter Rider on kotoba upstream). Remaining D2–D8
  + phased rollout R1..R7 unchanged.
- kotoba is dual-licensed Apache-2.0 + Charter Rider v2.0 at the workspace root,
  resolvable on standalone clone (real file, no escape symlink).
- The single-SHA2-256-CID fact is now reflected in kotoba's own docs.

## Incident post-mortem (transparency)

The first attempt at the submodule-pointer bump (step 5) used a `git worktree add
--no-checkout` whose **index was empty**; `git commit` therefore produced a
**destructive empty-tree commit** deleting all 92,332 files. It was **caught
before any merge** by a pre-push diff sanity check (`HEAD files: 0` vs `main
files: 92332`). The broken branch was deleted on remote + local; the bump was
redone correctly by populating the index with `git read-tree origin/main` and
verifying the diff was exactly the `40-engine/kotoba` gitlink (1 file) before
committing. **main was never affected.** Lesson: when committing in a
`--no-checkout` worktree, `git read-tree <ref>` first, and always diff
`HEAD vs origin/main --stat` before pushing a plumbing-built commit.

## Concurrency note

A background `/loop` was committing to `feat/social-security-for-humanity`
throughout the session. All substrate/closure work was done in **isolated git
worktrees off `main`** (or a fresh kotoba clone) and landed via PR to avoid the
shared-working-tree corruption + `reset --hard` race documented in the repo's
own history (PR #254 loss).

# Out of scope / follow-ups

- `audit-health` remains red on **unrelated** pre-existing debt (main is red on it
  independently): `dependabot-defunct` (`50-infra/l2-anchor-contract/lib/forge-std`),
  `sdk-exports-dist` (missing `./dist/*` targets), stale subrepo URLs
  (`kami-engine-sdk/.gitrepo` 404 in CI), and the `all.sh` rollup baseline. These
  need SDK-dist build / dependabot-config / subrepo cleanup, not Charter Rider work.

# References

- ADR-2605312345 — kotoba Datom first-class canonical state
- ADR-2605262130 — Kotoba canonical storage substrate (D1 satisfied by this session)
- ADR-2605302200 — kotoba multimodal cross-modal search
- ADR-2605192200 — etzhayyim Charter Compliance Rider v2.0
- kotoba PRs #10, #11; root PRs #301, #302, #304
