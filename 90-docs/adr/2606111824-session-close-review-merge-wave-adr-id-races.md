---
id: adr-2606111824-session-close-review-merge-wave-adr-id-races
title: "ADR-2606111824: Session close — review-and-merge wave (7 root PRs + 3 kotoba PRs) + ADR-id race ×2 renumber pattern"
status: accepted
doc_type: adr
topic: session-close-review-merge-wave
authoritative: false
last_verified: 2026-06-11
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "non-authoritative session-close index; the one normative output is the ADR-id race handling pattern (§3)"
authoritative_for: []
depends_on:
  - adr-2606111640 # portfolio QA wave (SDK deflake + kotoba coverage/CI) — same day, prior session
related:
  - adr-2606112201 # kaiyaku (renumbered in this wave)
  - adr-2606112301 # tate (renumbered in this wave)
  - adr-2606112200 # ehyeh doctrine (race counterpart)
  - adr-2606112300 # mimamori (race counterpart)
supersedes: []
superseded_by: []
---

# ADR-2606111824: Session close — review-and-merge wave + ADR-id race handling

**Status**: accepted (non-authoritative session index; §3 is the normative takeaway)
**Date**: 2026-06-11
**Deciders**: Jun Kawasaki

# Context

The founder asked for an honest portfolio maturity audit, then directed three
"review and merge" passes over the day's open PRs. Multiple Claude agents were
authoring concurrently (kaiyaku/tate, doctrine, cleanroom, crypto, mimamori),
which produced two classes of cross-agent collision this ADR records.

# Decision (what landed)

## 1. Merged this wave (etzhayyim/root)

| PR | Content | Review outcome |
|---|---|---|
| #1613 | `@etzhayyim/sdk` quorum-test deflake + stale libsignal CI note cleanup | merged (prior session, ADR-2606111640) |
| #1615 | ADR-2606111640 registration | merged |
| #1617 | mst-projector tsc fix — init the kotoba submodule in CI (root cause: the `workspace:*` dep lives inside the submodule) | reviewed sound; merged by founder |
| #1618 | kotoba submodule bump | **defective**: pinned gitlink `46e0bdaa6a27…` does not exist on the kotoba remote (pre-push local object); merged before the review comment landed → main unclonable |
| #1619 | corrected bump to the pushed `46e0bdaa83c4` (verified fetchable + `cargo metadata` at both workspace roots) | merged — repaired main |
| #1622 | kami-engine-sdk workflow: init kotoba submodule for the workspace `pnpm install` (`ERR_PNPM_WORKSPACE_PKG_NOT_FOUND`) | merged; the job passed on its own PR (first green since the dep appeared) |
| #1620 | cleanroom L5 wave (autoware/apollo_auto/ibm_qiskit/freee) | reviewed: gemini-CLI is a dev-time research tool with independent re-fetch verification, NOT a runtime inference path — Murakumo-only invariant (ADR-2605215000) holds; merged |
| #1623 | ehyeh 非二元神論 + yir'ah doctrine (Tier-1) + paper | reviewed: non-eschatology §1.15 intact, Tier-0 untouched, ratification claim procedurally valid (founder 1/1); merged |
| #1625 | argon2id-v1 KDF seam + yoro zk migration | reviewed in code: fail-closed `kdfName` dispatch (absent→PBKDF2 read-compat, unknown→throw), params AAD-bound; merged |
| #1626 | kaiyaku 解約 R0 (renumbered 2606112200→**2606112201**) | supersedes the kaiyaku half of #1624; merged |
| #1628 | tate 盾 R0 (renumbered 2606112300→**2606112301**) | supersedes the tate half of #1624; merged |

kotoba (same day, ADR-2606111640): #104 coverage harness + 78.75%-line
baseline, #105 first CI, #108 workflow-YAML hotfix + ADR — all merged; main
push run green (4m18s).

## 2. Two incident patterns this wave

**(a) Unfetchable gitlink (#1618).** A submodule bump pinned a local
pre-amend object. Merged, it broke every clean checkout AND the new CI
submodule steps. Detection is one API call:
`gh api repos/<owner>/<repo>/commits/<sha>` → 422 = do not merge.
Review rule: **a gitlink PR is unreviewable until the pinned SHA is fetchable
from the submodule's configured remote.**

**(b) ADR-id race ×2 (#1624 vs #1623; #1624-tate vs mimamori).** Two agents
forward-dated their ADR ids to the same round numbers (2200, 2300) instead of
using actual JST creation time (90-docs/CLAUDE.md convention). Both races were
resolved by the **renumber-supersede pattern** (§3).

## 3. ADR-id race handling pattern (normative)

When an open PR's ADR numeric id collides with an id already on main:

1. Do NOT push to the colliding PR's branch (1 branch = 1 owner).
2. Fresh worktree off `origin/main` → `cherry-pick` the PR's commits
   (authorship preserved).
3. Renumber to the next free id: ADR filename + front-matter `id`/`title` +
   every citation in the actor's manifest/CLAUDE.md/methods/tests/seeds +
   cross-actor references. **Scope the sed**: unrelated same-number references
   must survive (this wave: mimamori's "ADR-2606112200 D6" cites the ehyeh
   doctrine and a naive repo-wide sed would have clobbered it — scope to the
   added lines/files only, then diff against main to prove zero collateral).
4. Re-run the actor's tests post-renumber; regenerate the registry sidecars
   against current main; add the index row if the original PR missed it.
5. Open the superseding PR, close the original with a full accounting —
   **after re-checking the original branch for commits added since the
   cherry-pick** (this wave: tate was pushed onto kaiyaku-r0 mid-supersede and
   was nearly dropped; the close comment must enumerate exactly what landed
   where).

Prevention (recommended follow-up, not implemented here): a pre-commit /
PR-gate check that rejects a new `90-docs/adr/<id>-*.md` whose numeric id
already exists on the base branch, and **use actual JST creation time** for
ids (forward-dating to round numbers is what manufactured both races).

# Consequences

- All four actor/doctrine/crypto work-streams of 2026-06-11 are on main with
  zero dropped commits; the ADR index, registry sidecars (941 entries) and
  roster rows are consistent.
- The id space now contains two deliberate `+1` ids (2606112201, 2606112301)
  marking resolved races — unlike the unresolved 2605263400/2605263500 pair,
  these do not share a numeric id with their counterparts.
- root has no known red CI: the submodule-init series (#1617 → #1619 → #1622)
  closed the mst-projector tsc and cyber-drill `pnpm install` failures.

# Alternatives Considered

- **Merging colliding ADR ids as-is** (the 2605263400 precedent tolerates it):
  rejected — registry queries and `depends_on` references become ambiguous,
  and the debt note explicitly asks for reconciliation, not growth.
- **Asking PR owners to renumber their own branches**: rejected for this wave
  — both owner agents were mid-flight; the renumber-supersede keeps velocity
  without touching their branches.

# References

- ADR-2606111640 (portfolio QA wave — same day, prior session)
- PRs: #1613 #1615 #1617 #1618 #1619 #1620 #1622 #1623 #1624 #1625 #1626 #1628
- kotoba PRs #104 #105 #108
- 90-docs/CLAUDE.md § ADR ID Convention (JST creation time)
