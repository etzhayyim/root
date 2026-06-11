---
id: adr-2606111011
title: "ADR-2606111011: Session-Close — land feat/hydrogen-electrolysis-cfe-session-close → main (163-L5 cleanroom corpus reaches trunk)"
status: accepted
doc_type: adr
topic: session-close-land-hydrogen-branch-to-main
authoritative: true
last_verified: 2026-06-11
priority: 5.0
axis: process
weight: 0.50
priority_note: "Executes the tracked follow-up from ADR-2606110955: bring the long-lived feat/hydrogen-electrolysis-cfe-session-close branch (163-L5 cleanroom union + hydrogen/CFE work) back onto main. The branch was 64 ahead / 163 behind; main was merged into it and 14 conflicts hand-resolved before opening the branch→main PR."
authoritative_for:
  - session-close summary of the 2026-06-11 hydrogen-branch landing
  - record of the 14-file conflict resolution (8 manifests, kotoba submodule, L5 ledger, CLAUDE.md, deps.toml, registries)
related:
  - adr-2606110955-session-close-pr-backlog-review-merge
  - adr-2606082300-hydrogen-electrolysis-cfe-actor-kami-kotoba
supersedes: []
superseded_by: []
depends_on:
  - ADR-2606110955 (the follow-up this executes)
---

# ADR-2606111011: Session-Close — land the hydrogen-electrolysis branch onto main

**Date**: 2026-06-11
**Status**: ACCEPTED (process record)
**Deciders**: Jun Kawasaki

# Context

ADR-2606110955 closed the PR-backlog sweep with one explicit follow-up: the cleanroom
**163-L5 union** (and the rest of the hydrogen/CFE work) lived only on
`feat/hydrogen-electrolysis-cfe-session-close` — `main`'s cleanroom index was still far
behind. Founder direction this session: **land that branch onto `main`**.

The branch had diverged hard: **64 commits ahead, 163 behind**, 657 files different
(~127k insertions). The safe direction is to merge `main` **into** the branch, resolve,
then open a `branch → main` PR — which is what this session did.

# What was done

`git merge origin/main` into the branch surfaced **14 conflicts**, all hand-resolved
(registries regenerated, never hand-edited):

| conflict | resolution | why |
|---|---|---|
| 8 × `20-actors/*-compat/manifest.json` (arxiv_api, crossref, doi_system, ietf_rfcs, ncbi, orcid, pubmed, w3c_specs) | **branch** side | branch carries the L5 `verified` provenance block; main had `verified: null` |
| `40-engine/kotoba` (submodule gitlink) | **branch** ptr `92461b7346` | branch updated it later (17:53 vs main 16:51) to a real, fetchable commit; main's `98f9d2b3fd` is not resolvable on the kotoba remote |
| `00-contracts/schemas/cleanroom-l5-verification.json` | **branch** (163 L5) | branch is a strict superset of main's 42 L5 (0 actors in main absent from the branch); index auto-merged to L5 163 / L4 837, verified 0-drift vs the ledger |
| `CLAUDE.md` (kanjō row) | **main** side | main's row is newer (R0+R1 live EDGAR leg, 06-10); branch was stale on that one row |
| `deps.toml` (3 regions: niyaku/uchiwake/ibuki/rasen blocks + rasen GO-pathway notes) | **main** side | branch was simply behind; main's entries are additive/newer and include ADR-2606110955's own registration. No new duplicate ADR ids introduced (merged 13 dups == main's 13, all pre-existing) |
| `90-docs/_registry/{docs.json,graph.jsonld}` | **regenerated** | derived sidecars; freshness hooks pass (924 entries) |

Pre-commit hooks (registry/graph freshness, id-filename, relation-integrity,
registry-schema, secret-scan, charter gates, …) all green on the merge commit.

# Consequences

- The branch now contains `main` ∪ (branch-unique hydrogen/CFE + 163-L5 work); a
  `branch → main` PR carries it to trunk. Once merged, `main`'s cleanroom corpus reaches
  **163 L5 / 837 L4** (15.0%+ of the 1,000-actor corpus, up from 42).
- The 8 scholarly actors keep their L5 `verified` provenance; the kotoba submodule lands
  on a real, fetchable pin.
- No code authored this session — only the merge resolution + this record. Every merged
  change kept its own invariants (no-server-key, Murakumo-only, dry-run/operator-gated).
- The 13 pre-existing duplicate ADR ids in `deps.toml` are unchanged by this merge and
  remain a separate, pre-existing cleanup item (not introduced here).

# Follow-ups (tracked)

1. **Merge the `branch → main` PR** (this session opens it; CI must be green).
2. **De-dup the 13 pre-existing duplicate ADR ids** in `deps.toml` — a standalone hygiene
   pass, unrelated to this landing.
3. **Re-home the cleanroom L5 line onto `main`** going forward, so the ledger stops
   diverging on a long-lived feature branch (the root cause of this large reconciliation).

# References

- ADR-2606110955 (the follow-up this executes) · ADR-2606082300 (hydrogen-electrolysis CFE actor)
- Branch `feat/hydrogen-electrolysis-cfe-session-close` ·
  `00-contracts/schemas/cleanroom-l5-verification.json` (163 L5)
