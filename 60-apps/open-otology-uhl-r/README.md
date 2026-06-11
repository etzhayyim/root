---
id: open-otology-uhl-r-readme
title: open-otology-uhl-r — RW-free AppView for uhl-right-neural Pregel
status: active
doc_type: how-to
topic: open-otology-uhl-r-appview
authoritative: true
last_verified: 2026-05-18
related:
  - ../../90-docs/adr/2605181000-uhl-right-neural-project.md
  - ../../90-docs/adr/2605181040-uhl-medical-institution-registry.md
  - ../../50-infra/k8s/lg-uhl-right-neural/README.md
---

# open-otology-uhl-r

公開 RW-free AppView for the `uhl-right-neural` project (先天性右側感音難聴
neural軸 治療研究 Pregel). Charter: **ADR-2605181000**.

## What it is

A Cloudflare Worker exposing 1 XRPC method that wraps the in-cluster
LangServer (`lg-uhl-right-neural`) and validates input/output against the
authoritative Lexicon at
`00-contracts/lexicons/jp/etzhayyim/med/uhl/institution/matchQuery.json`.

| XRPC NSID | Type | Purpose |
|---|---|---|
| `jp.etzhayyim.med.uhl.institution.matchQuery` | query | substrate class × locale × DFNB9 gate → ranked institutions |

Per ADR-2605181040/1050/1060, the response always carries:

```json
{
  "requiresHumanReview": true,
  "ethicsCommitteeRequired": true,
  "dataExportRequiresReview": true
}
```

The Worker enforces these as `const: true` from the Lexicon schema.

## Why a thin AppView (not direct LangServer access)

1. **Lexicon enforcement**: every request validates against the AT Proto
   Lexicon — same contract surface used by other 60-apps.
2. **DID-addressable**: the AppView publishes `did:web:open-otology-uhl-r.etzhayyim.com`
   so other actors can `Invoke()` it across the substrate.
3. **Audit boundary**: every match request becomes an `at://` record
   (no PII per ADR-2605181040), so the project produces an auditable trail.
4. **Federation**: AT Proto firehose subscribers can react to match events
   (with the same human-review enforcement) without touching the cluster.

## Files

| File | Role |
|---|---|
| `PROJECT.jsonld` | Project metadata |
| `worker/kotodama.jsonld` | Worker app metadata (consumed by `etzhayyim deploy`) |
| `worker/src/app.ts` | XRPC handler skeleton (P0 stub — proxies to langserver) |
| `worker/package.json` | Worker dependencies |

## P0 status (this PR)

- **Skeleton only.** Handler wiring + Lexicon binding + DID config are in place.
- Real langserver proxy and atrecord audit emission are P1 deliverables.
- No UI in P0. P1 adds an embeddable Svelte UI for clinician review.

## Deploy (when implemented)

```bash
cd 60-apps/open-otology-uhl-r/worker
e7m actor build .
e7m actor deploy .
```

## Test

```bash
# Query for nerve aplasia + JP locale
curl -fsS 'https://open-otology-uhl-r.etzhayyim.com/xrpc/jp.etzhayyim.med.uhl.institution.matchQuery?substrateClass=nerve_aplasia&localeCountry=JP'
```
