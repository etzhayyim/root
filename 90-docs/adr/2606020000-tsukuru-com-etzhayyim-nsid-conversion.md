---
id: adr-2606020000-tsukuru-com-etzhayyim-nsid-conversion
title: "ADR-2606020000: tsukuru NSID conversion com.etzhayyim.apps.tsukuru.* → com.etzhayyim.apps.tsukuru.*"
status: proposed
doc_type: adr
topic: tsukuru-com-etzhayyim-nsid-conversion
authoritative: true
last_verified: 2026-06-02
priority: 6.0
axis: organization
weight: 0.60
priority_note: "Operator-directed repo-wide NSID conversion of tsukuru from the com.etzhayyim.* standard to com.etzhayyim.*, to match the hakken ingest actor (ADR-2606011700). Mechanical 87-file rename; no behavioural change."
authoritative_for:
  - tsukuru record/lexicon NSID namespace (com.etzhayyim.apps.tsukuru.*)
depends_on:
  - adr-2606011700-hakken-etzhayyim-migration-override
overrides:
  - repo-wide com.etzhayyim.apps.* standard, for the tsukuru namespace only (operator-directed)
---

# ADR-2606020000: tsukuru NSID conversion `com.etzhayyim.apps.tsukuru.*` → `com.etzhayyim.apps.tsukuru.*`

## Status

Proposed (2026-06-02). Operator-directed. Follow-up to ADR-2606011700 (hakken).

## Context

The hakken ingest actor was landed under `com.etzhayyim.apps.hakken.*` per operator direction
(ADR-2606011700), chosen with full knowledge that the repo standard is `com.etzhayyim.apps.*`
(15,758 occurrences vs 0 for `com.etzhayyim.*`; `com.etzhayyim.*` is otherwise launchd labels).

Meanwhile `main` had independently migrated tsukuru to `com.etzhayyim.apps.tsukuru.*` (~86 files).
Leaving tsukuru on `com.etzhayyim.*` while hakken (its sibling OEM-discovery actor) is on
`com.etzhayyim.*` would split the two ingest actors across namespaces. The operator directed that
tsukuru be converted to `com.etzhayyim.apps.tsukuru.*` to match hakken — deliberately, accepting
the divergence from the repo-wide `com.etzhayyim.*` standard.

This is the dedicated follow-up PR that ADR-2606011700 deferred (the hakken PR stayed hakken-only
to avoid bundling an 86-file override of merged work).

## Decision

Convert every `com.etzhayyim.apps.tsukuru.*` reference to `com.etzhayyim.apps.tsukuru.*`
repo-wide (87 files), and relocate the tsukuru lexicons accordingly.

1. **Lexicon ids + dirs.** 46 lexicons: `id` field `com.etzhayyim.apps.tsukuru.*` →
   `com.etzhayyim.apps.tsukuru.*`; directory `git mv`
   `00-contracts/lexicons/com/etzhayyim/etzhayyim/apps/tsukuru/` →
   `00-contracts/lexicons/com/etzhayyim/apps/tsukuru/` (clean path, matching hakken; the old path
   carried a spurious `etzhayyim` segment the id never had). Catalog `git mv`
   `00-contracts/catalogs/com/etzhayyim/tsukuru/` → `00-contracts/catalogs/com/etzhayyim/tsukuru/`.

2. **Source + cross-app refs.** rw-free, orchestration scripts, `kotodama.toml`, `20-actors/tsukuru`,
   and cross-app callers (`aidesk`, `hc`, `open-robo`, kotodama cells, graph seed migrations, ADRs)
   all updated. This avoids a split-collection bug (one writer on `com`, another on `app`).

3. **Payment stays shared.** `com.etzhayyim.apps.payment.*` (escrowOpened / escrowRefunded / sent,
   read by treasury / tithe) is owned by a different authority and is **NOT** renamed. Only the
   `.tsukuru` token moved; payment is untouched.

4. **Generated artifacts.**
   - `10-protocol/lexicons-bundle/src/lexicons.gen.json` — **regenerated** (`build-bundle.mjs`),
     scans lexicon ids; without this the PDS validator hangs with `Lexicon not found`.
   - `_manifest.json`, `apps.openapi.json`, `docs.json`, `graph.jsonld`,
     `bpmn-coverage-manifest.json`, `process-catalog.v1.json` — updated with a **contained
     token+path swap** to keep the diff minimal and correct for the tsukuru change. A full
     re-run of the registry generators (`regen-registry.py`, `regen-graph-jsonld.py`,
     `gen-tool-manifest.mjs`, etc.) by CI/maintainer is recommended to confirm no drift.

## Consequences

- **87 files** changed, symmetric (pure rename/token swap); no behavioural change.
- tsukuru + hakken now share the `com.etzhayyim.apps.*` namespace.
- **Divergence from repo standard:** tsukuru/hakken are now the only `com.etzhayyim.apps.*`
  record actors in a repo otherwise standardised on `com.etzhayyim.apps.*`. This is deliberate
  and operator-directed; the `com.etzhayyim.*` vs `com.etzhayyim.*` record-NSID convention still
  needs an org-level ruling (carried from ADR-2606011700). If the org standardises on
  `com.etzhayyim.*`, both tsukuru and hakken revert in one sweep.
- **Deploy prereq:** PDS typed-registry regen (`gen-pds-lexicon-registry.mjs`) + Worker redeploy
  before tsukuru serves on the new NSID.

## References

- ADR-2606011700 — hakken etzhayyim migration (com.etzhayyim, the trigger for this alignment)
- ADR-2605202800 — tsukuru full move to etzhayyim (business-model-change)
