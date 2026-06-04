---
id: adr-0061
title: Tsukuru ISIC BPMN Actors
status: active
doc_type: adr
topic: tsukuru
authoritative: true
last_verified: 2026-04-27
authoritative_for:
  - com.etzhayyim.apps.tsukuru.industryActor.*
  - tsukuru-isic-bpmn-actors
  - tsukuru-euv-bpmn-actors
  - com.etzhayyim.apps.tsukuru.euv.*
  - com.etzhayyim.apps.tsukuru.supplierExchange.*
related:
  - 0056-bpmn-as-actor
  - 0060-tsukuru-industry-profile-catalog
supersedes: []
superseded_by: []
---

# Context

`tsukuru.etzhayyim.com` already had an industry profile catalog, but the runtime
surface still centered on the controller DID `did:web:tsukuru.etzhayyim.com`.
That made it hard to expose sector-specific BPMN pipelines or to publish
stable actor identities for each industry view.

The repo already uses path-based DID publication for actor families and
ADR-0056 defines BPMN-as-actor as the preferred orchestration surface.
For tsukuru, the natural coarse-grained public split is the 21 top-level
ISIC sections (`A` through `U`).

# Decision

Publish one path-based actor DID per ISIC section under the tsukuru DID
root and pair each actor with one BPMN process in
`etzhayyim-root/00-contracts/bpmn/com/etzhayyim/tsukuru/`.

The authoritative catalog is the shared module
`60-apps/etzhayyim-project-tsukuru/appview/tsukuru-tsukr8u0/src/isic-industry-actors.mjs`.
From that catalog we derive:

- `20-actors/tsukuru/actor-manifest.jsonld` `actors[]` publication entries
- tsukuru public XRPC queries:
  - `com.etzhayyim.apps.tsukuru.industryActor.getIndustryActor`
  - `com.etzhayyim.apps.tsukuru.industryActor.listIndustryActors`
- `60-apps/etzhayyim-project-tsukuru/scripts/register-isic-industry-actors.mjs`
- one BPMN process per ISIC section

# Design

Each ISIC actor exposes:

- `sectionCode`
- `actorDid`
- `actorPath`
- `bpmnProcessId`
- `cron`
- `industryCodes[]`

The BPMN pattern for each section is intentionally narrow:

1. timer start on a section-specific staggered daily cron
2. `generic.db.select` over `vertex_other` to sample matching
   `TsukuruManufacturer` rows by `industryCode`
3. `generic.audit.emit` using the section actor DID as `actor`

This keeps the BPMN surface deployable through the generic Zeebe worker
without adding section-specific Python or Worker code.

# Consequences

Positive:

- `tsukuru` gains a public actor namespace aligned with a standard
  industry taxonomy.
- BPMN orchestration is no longer only controller-DID scoped.
- publication, registration, and XRPC discovery all share one catalog.

Tradeoffs:

- ISIC sections are broader than the current tsukuru profile model, so
  some sections map to zero or few `industryCodes`.
- the first BPMN cut emits audit snapshots, not full sector analytics.
  Richer section-specific flows can extend these processes later.

# 2026-04-27 Update: EUV Design/Manufacturing BPMN Actors

`tsukuru.etzhayyim.com` now has a semiconductor EUV design/manufacturing lane
under the ISIC C actor owner DID `did:web:tsukuru.etzhayyim.com:industry:isic:c`.
This lane keeps the broad ISIC section actors from this ADR, but adds
specialized BPMN actors for the high-value EUV workflow and supplier CAD/RFQ
boundary.

## Added BPMN actor bindings

| Process | NSID | Purpose |
|---|---|---|
| `tsukuru_euv_lithography_manufacturing_flow` | `com.etzhayyim.apps.tsukuru.euv.designManufacturingFlow` | Design EUV lithography manufacturing phases and CAD/CAM handoff gates |
| `tsukuru_normalize_supplier_exchange_package` | `com.etzhayyim.apps.tsukuru.supplierExchange.normalizePackage` | Normalize AutoCAD/Fusion/STEP/IGES/glTF artifacts into a supplier exchange envelope |
| `tsukuru_validate_supplier_exchange_package` | `com.etzhayyim.apps.tsukuru.supplierExchange.validatePackage` | Validate EUV supplier readiness and return `ready/blockers` without writing records |
| `tsukuru_prepare_euv_order_package` | `com.etzhayyim.apps.tsukuru.euv.prepareOrderPackage` | Compose EUV flow and supplier exchange package in one call |
| `tsukuru_get_euv_implementation_coverage` | `com.etzhayyim.apps.tsukuru.euv.getImplementationCoverage` | Report implementation coverage, manifest checks, score, and required capabilities |

The graph seed is
`30-graph/graph-schema/migrations/20260427011500_seed_tsukuru_euv_bpmn_actor.ts`.
The coverage SSoT is `70-tools/config/bpmn-coverage-manifest.json`, where
`tsukuru-euv` currently has 5 bindings.

## Supplier exchange boundary

Supplier exchange is deliberately modeled as a boundary envelope rather than
native CAD kernel state. The accepted design handoff surface includes:

- AutoCAD references: `autocad-dwg-reference`, `autocad-dxf`
- Fusion 360 references: `fusion360-archive-reference`,
  `fusion360-assembly-archive-reference`
- Neutral exchange: `step`, `iges`, `gltf`
- Supplier RFQ envelope: `tsukuru-alibaba-supplier-rfq-json`

Validation requires at minimum an AutoCAD reference, a Fusion 360 reference,
an Alibaba-style RFQ envelope, `overlay_nm`, and `cleanroom`. Missing inputs
are returned as explicit blockers by
`com.etzhayyim.apps.tsukuru.supplierExchange.validatePackage`.

## Coverage contract

`com.etzhayyim.apps.tsukuru.euv.getImplementationCoverage` is the runtime-readable
coverage contract for this lane. It returns:

- `coverageManifest[]` with BPMN source path and lexicon path per actor
- `manifestChecks[]`, `manifestStatus`, `missingManifestItems`, and
  `coverageScore`
- required capabilities such as `supplier-package-validation`,
  `autocad-reference-handoff`, `fusion360-reference-handoff`, and
  `alibaba-style-rfq-envelope`

This complements the static gates:

- `pnpm --silent lint:bpmn:coverage:json`
- `pnpm --silent lint:bpmn:worker-tasks:json`
- `pnpm lint:nsid:exists`
- `pnpm exec vitest run 60-apps/etzhayyim-project-tsukuru/appview/tsukuru-tsukr8u0/src/app.test.ts`
