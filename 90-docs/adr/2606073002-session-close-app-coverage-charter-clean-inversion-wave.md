---
id: adr-2606073002-session-close-app-coverage-wave
renumbered_from: "2606073000"
title: "ADR-2606073002: Session close — app-coverage charter-clean inversion wave + substrate-remediation ratchet"
status: active
doc_type: adr
topic: session-close-app-coverage-wave
authoritative: false
last_verified: 2026-06-07
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for: []
depends_on:
  - 2606071400
  - 2606071500
  - 2606071600
  - 2606071800
  - 2606072000
  - 2606072200
  - 2606072400
  - 2606072600
  - 2606072800
related: []
supersedes: []
superseded_by: []
---

# ADR-2606073002: Session close — app-coverage charter-clean inversion wave + substrate-remediation ratchet

**Status**: active (documentation-only closure)
**Date**: 2026-06-07
**Deciders**: Jun Kawasaki

# Context

Answers the question *「いまの actor で uber, flight scanner, airbnb, hotels, google, sales force,
office 365, shopofy などと同等の app の設計、実装 coverage は?」* (coverage of the eight named
mainstream apps) and the follow-up directive to **raise that coverage and maturity** over a
self-paced `/loop`.

The audit found: design coverage was broad but real implementation was thin, and — critically —
**a faithful clone of each app is charter-forbidden** (gig labour, OTA commission, ad-funded
search, multi-tenant SaaS billing, content mining are all prohibited by the Charter §1.3/§1.13).
So each gap is closed as a **charter-clean inversion** (the method `okaimono` used to invert
Amazon): each prohibited term is replaced by its charter-aligned dual, made **structurally
unrepresentable** (the forbidden field does not exist in any lexicon), not merely policy-blocked.

The audit also surfaced a standing substrate-boundary violation: the pre-commit lint only gated
*staged* files, so a large body of pre-guard legacy code still read through RisingWave/Hyperdrive/
Kysely unchecked.

# Decision (what landed — PR #1352, branch `worktree-app-coverage-abc`)

**All eight named apps now have charter-clean inversions:**

| App | Actor | ADR | Charter-clean core (structurally unrepresentable) |
|---|---|---|---|
| Uber | **ainori 相乗** (new) | 2606071500 | no gig wage (`driverWage≡0`), no surge (cost_share has no demand param), no person-tracking; reuses todoke route core (parity-pinned) |
| Flight scanner | **tsubasa 翼** (new) | 2606072800 | no affiliate/commission (`≡0`), member self-books, CO₂ surfaced on every result, no urgency field |
| Airbnb / Hotels | **shukubo 宿坊** (new) | 2606071600 | zero commission, no-double-book, no discriminatory score field, no in-stay surveillance |
| Shopify | **omise 御店** (legacy→kotoba) | 2606071400 | zero commission/subscription, no-oversell, okaimono Ring-1-coherent, member-signed |
| Salesforce/SAP | **business-manager** (legacy→kotoba) | 2606072000 | internal-only, double-entry-balanced, derived approval, append-only audit trail |
| Calendly | **yotei** (legacy→kotoba) | 2606072200 | free, no-double-book, no booker-harvest, member-signed |
| Google Drive | **organizer** (legacy→kotoba) | 2606072400 | content-addressed dedup, vault-isolation, no content mining |
| Indeed/LinkedIn | **talent** (legacy→kotoba) | 2606072600 | self-sovereign, Signal-E2E PII, k-anonymity, GDPR Art-17 hard delete |

(Google search/maps + Office-365 mail were already covered by kotoba-search/maps + m365-ingest.)

**Substrate-remediation wave (ADR-2606071800)** — the keystone guard:
- `substrate-remediation-audit.mjs` — full-tree shrink-only ratchet (`--audit` FAILS on any
  storage-boundary violation absent from the frozen allowlist; WARNs on graduated entries).
  Wired as a `pre-push` lefthook command.
- `substrate-frozen-allowlist.json` — seeded at 124 files; **shrunk to 101** when a sibling
  yatabase cleanup deleted 23 (the ratchet flagged them graduated, demonstrating the mechanism).
- `substrate-boundary.mjs` (pre-commit) extended to grandfather frozen-legacy storage violations
  to a warning (so unrelated edits aren't blocked) while still hard-blocking new files.

**Maturity:** every new + converted actor reached tested R1; all seven app-actors were deepened
(business-manager: invoice AP/AR + budget-vs-actual; shukubo: lodging no-double-book + host;
omise: no-oversell + fulfilment; yotei: cancel + reschedule; organizer: collection ops + batch
auto-organize; talent: enrichment + listOccupations; ainori: end-to-end plan_pooled_trip
composing the reused todoke route with no-surge cost-share, no-profit invariant).

**~165 unit tests green** across the wave; every commit kept the substrate audit clean.

# Consequences

- The eight-app coverage question is answered concretely: not "build the clone" but "build the
  charter-clean inversion", with the prohibition encoded in the schema.
- The substrate-boundary violation is now a tracked, CI-ratcheted, shrink-only debt (101 → 0
  target), enforced tree-wide rather than only on new diffs.
- ZERO Charter invariant amendments — every gate derives from existing Tier-0 priorities.

# Honest scope / follow-ups

- All new/converted actors are **R0/R1**: deterministic logic + tests; live settlement, dispatch,
  ingest, and external booking are operator/Council-gated per each actor's gates (intent-only).
- Legacy `actor-manifest.jsonld` scaffolds are marked DEPRECATED (retained one R-cycle).
- **Phase B not started**: the 101 frozen legacy files still read through Hyperdrive — each
  migrates to `kotoba-kqe` in its own scoped PR (the ratchet keeps the count shrink-only).
- Authoritative per-actor design lives in each actor's ADR (linked above).

# References

- ADR-2606071400/500/600/800, 2606072000/200/400/600/800 — the wave's ADRs
- ADR-2606012100 — okaimono (the inversion-method exemplar)
- ADR-2605262130 / 2605312345 — kotoba substrate (the boundary)
- PR #1352
