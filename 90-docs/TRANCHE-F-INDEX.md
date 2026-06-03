---
id: doc-tranche-f-index
title: "Tranche F closure docs — operator navigation index"
status: active
doc_type: reference
topic: tranche-f-index
authoritative: false
last_verified: 2026-05-21
priority: 6.5
axis: operations
weight: 0.30
priority_note: "Single-page index for the 6 Tranche F closure docs landed during the 2026-05-21 session. Pure navigation — no decisions, no canonical content. Operators land here first to find the right doc for their current step."
authoritative_for:
  - navigation between Tranche F closure artifacts
depends_on: []
related:
  - adr-2605212100-magatama-worker-3-axis-tranche-f-closure
  - adr-2605211757-dns-cutover-runbook-etzhayyim-ai-to-etzhayyim-com
  - adr-2605211913-vendor-refactor-and-git-rm-phase-4-5-runbook
  - adr-2605211925-phase-6-archive-markers-runbook
  - doc-2605211800-vendor-importer-survey-gate-d
  - doc-2605211900-tranche-f-all-gates-closure-confirmation
  - doc-2605211949-gate-a-execution-checklist
supersedes: []
superseded_by: []
---

# Tranche F closure docs — operator navigation index

**Date**: 2026-05-21

This page is the navigation hub for the 6 closure docs landed during the
2026-05-21 session. Pick the row matching your current task.

## "I want to…" → "Read this"

| What you want to do | Where to start |
|---------------------|----------------|
| Understand the org-split context first | etzhayyim-side `ADR-2605152100` (root cutover ADR) |
| See the 3-axis classification for the 70 workers | etzhayyim-side `ADR-2605212100` §1 |
| Check current gate closure status at a glance | `90-docs/2605211900-tranche-f-all-gates-closure-confirmation.md` |
| Port a worker to RW-free SQLite (gate (a) execution) | `90-docs/2605211949-gate-a-execution-checklist.md` (42 rows) |
| Run the DNS cutover (gate (b)) | `90-docs/adr/2605211757-dns-cutover-runbook-etzhayyim-ai-to-etzhayyim-com.md` |
| Understand the deployment surface (gate (c)) | inline in the DNS runbook §0 + §3.1 (no separate ADR) |
| Find which vendor files need re-pointing (gate (d)) | `90-docs/2605211800-vendor-importer-survey-gate-d.md` |
| Execute Phase 4-5 vendor refactor + `git rm` | `90-docs/adr/2605211913-vendor-refactor-and-git-rm-phase-4-5-runbook.md` |
| Apply Phase 6 archive markers (final cleanup) | `90-docs/adr/2605211925-phase-6-archive-markers-runbook.md` |

## Doc-to-phase mapping (canonical)

```
ADR-2605152100 (org-split, 2026-05-15)
  └── Phase 1 catalog freeze ─────────── (historical; pre-session)
  └── Phase 2 scaffolding ────────────── (historical; pre-session)
  └── Phase 3 content copy ──────────── (Wave 2 26 repos archived 2026-05-17)
        Tranche F sub-gates:
        ├── (a) per-worker re-impl ──── 2605211949-gate-a-execution-checklist.md [42 rows OPEN]
        ├── (b) DNS cutover ────────── ADR-2605211757 [runbook ready]
        ├── (c) deployment surface ─── inline in ADR-2605211757 §0 + §3.1
        └── (d) vendor importer ───── 2605211800-vendor-importer-survey-gate-d.md
                                       + 3 lg relocates + 1 hume inline [done]
  └── Phase 4 vendor dep switch ────── ADR-2605211913 §1 [runbook ready]
  └── Phase 5 vendor open-scope deletion ── ADR-2605211913 §2 [runbook ready, gated on (a)]
  └── Phase 6 archive markers ──────── ADR-2605211925 [runbook ready, gated on Phase 5]

Snapshot of where each gate sits: 2605211900-tranche-f-all-gates-closure-confirmation.md
```

## Cross-repo pointers

- etzhayyim-side ADR-2605212100 §2 STATUS blocks were updated 2026-05-21 to match
  the honest framing here (🟡 PATTERN ESTABLISHED for gate (a), 🟡 INLINE for
  gate (c)).
- etzhayyim-side `deps.toml [[migrations]] etzhayyim-tranche-f-three-axis-split-2026-05-17`
  has 3 closure cross-reference fields pointing to this repo:
  ```toml
  gates_design_closed_at = "2026-05-21T17:57:00Z"
  closure_confirmed_by = "etzhayyim/root/90-docs/2605211900-tranche-f-all-gates-closure-confirmation.md"
  closure_evidence = [
    "etzhayyim/root/90-docs/adr/2605211757-dns-cutover-runbook-etzhayyim-ai-to-etzhayyim-com.md",      # gate (b) + (c)
    "etzhayyim/root/90-docs/2605211800-vendor-importer-survey-gate-d.md",                          # gate (d)
    "etzhayyim/root/90-docs/adr/2605211913-vendor-refactor-and-git-rm-phase-4-5-runbook.md",      # Phase 4-5
  ]
  ```

## File sizes (for quick triage)

| File | Lines | Read time |
|------|-------|-----------|
| `90-docs/adr/2605211757-...dns-cutover-runbook...md` | 431 | ~15 min |
| `90-docs/adr/2605211913-...phase-4-5-runbook.md` | 388 | ~13 min |
| `90-docs/adr/2605211925-phase-6-archive-markers-runbook.md` | 361 | ~12 min |
| `90-docs/2605211949-gate-a-execution-checklist.md` | (new, ~200) | ~7 min |
| `90-docs/2605211900-...closure-confirmation.md` | 159 | ~5 min |
| `90-docs/2605211800-...gate-d.md` | 99 | ~3 min |
| **Total** | ~1,640 | ~55 min |

A new operator can read the whole closure dossier in under an hour.

## Open execution items (NOT in this repo)

The runbooks live here; the executions live elsewhere:

1. **Per-worker RW-free Python ports** — to be committed to
   `etzhayyim/root/20-actors/magatama/py/src/pymagatama/` (this repo). The
   2026-05-21 session prototyped + reverted these; the gate (a) checklist
   provides the row-by-row acceptance criteria for the next attempt.
2. **DNS cutover Wave A → D** — Cloudflare zone + Mac mini fleet (live infra,
   operator-side).
3. **Vendor `git rm`** — `etzhayyim-root` repo, atomic per-category
   commits (vendor side).
4. **Phase 6 archive-marker stubs + `gh repo archive`** — `etzhayyim-root`
   subtrees + etzhayyim-org repos.

When each is done, fill the corresponding timestamp field in the etzhayyim-side
`deps.toml [[migrations]]` entry (see Phase 4-5 runbook §F + Phase 6 runbook §4).
