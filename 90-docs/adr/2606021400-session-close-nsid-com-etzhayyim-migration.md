---
id: adr-2606021400-session-close-nsid-com-etzhayyim-migration
title: "ADR-2606021400: Session close — repo-wide NSID migration com.etzhayyim.* / com.etzhayyim.* → com.etzhayyim.*"
status: active
doc_type: adr
topic: session-close-nsid-com-etzhayyim-migration
authoritative: false
last_verified: 2026-06-02
related:
  - adr-2606021200-himawari-solar-pv-manufacturing-r0
  - adr-2605172000-substrate-boundary-state
  - adr-2605172100-substrate-boundary-payment
supersedes: []
superseded_by: []
---

# ADR-2606021400: Session close — repo-wide NSID migration → com.etzhayyim.*

**Status**: active
**Date**: 2026-06-02
**Deciders**: Jun Kawasaki

Documentation-only closure for the PR-triage + NSID-migration session.

# Context

The repo carried two legacy lexicon/NSID namespaces — `com.etzhayyim.*` (the
atproto-convention `app.*` reverse-DNS) and the vendor-origin `com.etzhayyim.*` —
where the operating domain is `etzhayyim.com`, whose reverse-DNS is
`com.etzhayyim`. PR #718 had already converted the tsukuru actor
(`com.etzhayyim.apps.tsukuru.*` → `com.etzhayyim.apps.tsukuru.*`); this session
extended that to the whole tree.

# Decision

Migrate every first-party NSID / lexicon-id to **`com.etzhayyim.*`**, repo-wide,
as a deterministic mechanical transform (sed + `git mv`), not hand-edited or
agent-rewritten.

## Landed

- **#742 — repo-wide migration** (~23.4k files):
  - dotted ids `com.etzhayyim.` / `com.etzhayyim.` → `com.etzhayyim.`
  - slash path-strings `com/etzhayyim/` / `com/etzhayyim/` → `com/etzhayyim/`
  - `git mv` of every lexicon/contract dir tree (`bpmn`, `dmn`, `examples`,
    `formats`, `forms`, `lexicons`, `lexicons/archive`, + comfyui/murakumo app
    lexicon mirrors) under `…/com/etzhayyim/` and `…/com/etzhayyim/` →
    `…/com/etzhayyim/`.
  - Collisions: 128 app↔ai mirrored files byte-identical after transform →
    de-duplicated; 1 differing `murakumo/README.md` kept the app-origin copy.
  - **Excluded by design**: the protected Step-8-cutover paths
    `20-actors/magatama/py/` (609) + `50-infra/cluster/murakumo/` (4) per
    ADR-2605214000 §3 / ADR-2605215000 §4 (atomic rename
    post-legal-registration); historical docs (1,136 `.md`, incl. all ADRs, as
    as-of record); Android Java packages `…/java/com/etzhayyim/` (5, separate JVM
    namespace); and 40 files carrying pre-existing substrate-boundary
    violations (reverted to keep the rename un-entangled — same pattern as
    #718→#728).

- **#745 — migration-gap fixes** (surfaced by `monorepo-health` on the himawari
  re-land, which #742's merge never gate-checked):
  - **Segmented constructions** (20 src files) — `_LEX = … / "app" /
    "etzhayyim" / …` and `["ai","etzhayyim",…].join(".")`, which the plain
    dot/slash rewrite could not match.
  - **Escaped-dot regex literals** (19 files) — `r"app\.etzhayyim\.karute\.(\w+)"`,
    XRPC route matchers, Rego/yaml path policies.
  - Together these had broken the actor manifest-vs-disk + PHI-guard-coverage
    audits (watatsumi / tadori / tsukuroi / karute / …). `monorepo-health`
    green after the fix.

## Related work this session

- **himawari (向日葵)** solar-PV manufacturing Tier-B actor R0 (ADR-2606021200)
  re-landed onto `main` in the `com.etzhayyim.*` namespace (#745) after its
  origin branch (`feat/sarutahiko-truck-factory`) was found to have an
  **unrelated git history** with the reset `main` — re-applied as net-new
  content rather than a destructive cross-history merge.
- Dependabot bumps merged (#705–708, #711, #731, #732); #728 cleared a
  pre-existing dead-`psycopg` substrate-boundary violation; #738 tracks the
  #724 hakken `com.etzhayyim.*` → `com.etzhayyim.*` follow-up.

# Consequences

- **Partial-rename state (tracked)**: the excluded `magatama/py` + `murakumo`
  paths still reference old NSIDs/paths that moved; per ADR-2605214000 /
  ADR-2605215000 these reconcile in the atomic post-legal-registration cutover.
  Watch for runtime NSID-resolution misses in those actors until then.
- **CI gap noted**: the heavy `monorepo-health` / docs-freshness gates are
  path-routed and did not fire on the #742 merge, letting the segmented +
  escaped-dot drift land silently. Future large mechanical migrations should
  dispatch `audit-health.yml` explicitly before merge.
- **Un-landed net-new work** remaining on the orphaned branches:
  kotoba-browser-node (ADR-2606013600 — did-web `/actors`, yoro `kotoba-sw.js`)
  and the hakken `kami-engine-sdk` dir — to be re-landed by the same
  extract-and-reapply approach if wanted.

# Verification

- `nsid-lexicon-exists` OK (6738 lexicons) · 0 invalid lexicon JSON · 0 residual
  ids/paths outside the excluded zones · registries (`docs.json` /
  `graph.jsonld`) regenerated and `--check` in sync.
- `monorepo-health` green (workflow-dispatch confirmed on the fix head);
  `lint-and-test` (incl. substrate-boundary) + `docs-registry-freshness` green.
- Residual red = the pre-existing pnpm-install `vitest`/`tsc` infra-flake (red
  on `main` independently of this work).
