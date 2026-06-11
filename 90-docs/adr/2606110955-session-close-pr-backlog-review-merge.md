---
id: adr-2606110955
title: "ADR-2606110955: Session-Close — open-PR backlog review + merge (8 PRs); L5 ledger union to 163"
status: accepted
doc_type: adr
topic: session-close-pr-backlog-review-merge
authoritative: true
last_verified: 2026-06-11
priority: 5.0
axis: process
weight: 0.50
priority_note: "Session-close record for the review-and-merge sweep of the open-PR backlog on etzhayyim/root (7 PRs open at start + 1 opened mid-sweep). Five PRs carried merge conflicts that were resolved by hand (registry sidecars regenerated, not hand-edited); one (the L5 cleanroom ledger) required a genuine set-union rather than a side-pick."
authoritative_for:
  - session-close summary of the 2026-06-11 PR-backlog review + merge sweep
  - record of the cleanroom L5 ledger union (PR #1535: 150 base ∪ 155 head = 163 L5)
related:
  - adr-2606101845-session-close-infra-robotics-r1-device-in-the-loop
  - adr-2606102000-session-close-ibuki-digest-live-run-robustness
supersedes: []
superseded_by: []
depends_on: []
---

# ADR-2606110955: Session-Close — open-PR backlog review + merge

**Date**: 2026-06-11
**Status**: ACCEPTED (process record)
**Deciders**: Jun Kawasaki

# Context

Founder direction: *review and merge* the open PRs on `etzhayyim/root`. Seven were
open at the start of the sweep; an eighth (#1593) was opened mid-sweep and folded in.
The substance of each PR is authoritative in its own already-merged commit / ADR — this
record exists only to document the merge decisions, the conflict resolutions, and one
non-trivial set-union, so the next session can trust the resulting tree.

# What was done

**Merged into `main` (squash, repo convention), no conflicts:**

1. **#1590** — meeting-recorder appview `getMinutes` XRPC (read 議事録 from the graph).
2. **#1589** — yoro prod kotoba-sw verification script (Playwright, follow-up to #1587).
3. **#1593** — ibuki autonomous identity = a revocable CACAO-delegation leash
   (`delegation.py`, present-only, fail-open, stdlib-only; +16 tests). Reviewed: design
   is consistent with no-server-key (ADR-2605231525) — the organism never signs.

**Merged into `main` (squash) after hand-resolving conflicts:**

4. **#1498** — `deps.toml`: both sides appended distinct `[etzhayyim.milestones.*]` /
   `[[adrs]]` blocks → kept **both** (union; TOML re-validated).
5. **#1493** — supply-chain `NOTICE` rename/content conflict → took the supply-chain
   migration line; registry sidecars regenerated.
6. **#1568** — `CLAUDE.md` status table: the PR advances the **infra-robotics** row (its
   purpose — R1 device-in-the-loop, ADR-2606101430) while `main` had advanced the
   **ibuki** row (ecosystem, ADR-2606101800). Kept the PR's infra-robotics row **and**
   `main`'s newer ibuki row — not a blind side-pick.
7. **#1548** — ADR `README.md` index (union of both appended rows). Re-merged once
   because earlier merges had moved `main` between the mergeability check and the merge.

**Merged into `feat/hydrogen-electrolysis-cfe-session-close` (the PR's own base, NOT
`main`):**

8. **#1535** — cleanroom L5 +13 specialized + 5 general. The conflict in
   `cleanroom-l5-verification.json` + `cleanroom-actors.index.json` was **not** a
   side-pick: the PR head added 13 specialized actors (athenahealth, autodesk,
   benchling, bentley, cerner, drchrono, epic-systems, materials_project, miro, paystack,
   universal_robots, vimeo, x) while the base branch had **independently** added 8 others
   (kafka, mavlink_swarm, onnx_runtime, opc_ua, openxr, px4_autopilot, redis, ros2_nav),
   with 142 in common. The correct merge is the **set-union → 163 L5** (142 ∪ 13 ∪ 8),
   built programmatically by handle (head object preferred on overlap), with
   `tierCounts` reconciled to **L5 163 / L4 837** and the per-actor `index` tiers verified
   to match the ledger exactly (0 drift either direction).

For every conflict touching `90-docs/_registry/`, the sidecars were **regenerated**
(`regen-registry.py`, `regen-graph-jsonld.py`) rather than hand-edited, so the
`docs-registry-freshness` / `docs-graph-jsonld-freshness` pre-commit hooks pass.

# Consequences

- **0 open PRs remain** on `etzhayyim/root`.
- Every merge landed with **0 failing CI checks** (the `UNSTABLE` state was only
  non-required CodeQL / submit-pypi jobs still pending — identical to baseline).
- **The L5 corpus is split across branches**: `main` is at **34 L5** (its cleanroom
  index predates the L5 push); the **163 L5** union lives on
  `feat/hydrogen-electrolysis-cfe-session-close`. That branch must itself be merged to
  `main` for the corpus to reach 163 there — tracked as a follow-up, not done in this
  session.
- Invariants untouched: every merged change preserved its own constitutional guarantees
  (no-server-key, Murakumo-only, dry-run/operator-gated outward paths); this session
  added no code, only merge commits + this record.

# Follow-ups (tracked)

1. **Land `feat/hydrogen-electrolysis-cfe-session-close` → `main`** so the 163-L5 union
   (and the rest of that branch's electrolysis/CFE work) reaches the trunk; re-resolve
   the cleanroom index/ledger against `main`'s 34-L5 state at that time.
2. **#1535 was a non-main-base PR** — confirm whether the cleanroom L5 line should keep
   basing off the hydrogen branch or re-home onto `main` to avoid future divergent-append
   conflicts in the ledger.

# References

- PRs #1590 #1589 #1498 #1493 #1568 #1548 #1593 (→ main) · #1535 (→ feat/hydrogen-…)
- `00-contracts/schemas/cleanroom-l5-verification.json` ·
  `00-contracts/schemas/cleanroom-actors.index.json`
- ADR-2606101845 · ADR-2606102000 (session-close precedent)
