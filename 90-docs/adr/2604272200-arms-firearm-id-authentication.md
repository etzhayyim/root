---
id: adr-2604272200-arms-firearm-id-authentication
title: "ADR-2604272200: Arms firearm ID authentication system"
status: active
doc_type: adr
topic: arms-firearm-id-authentication
authoritative: true
last_verified: 2026-04-28
authoritative_for:
  - arms.etzhayyim.com DID challenge-response holder authentication
  - firearms chain-of-custody tracking (vertex_arms_*)
  - Tier 3 PII split for serial/permit numbers (ADR-0018)
  - defence cluster incident integration (vertex_open_defence_event)
  - export control gate (ATT/Wassenaar, HTTP 451)
related:
  - adr-0036-worker-direct-hyperdrive-persistence
  - adr-0018-pii-tier3-cohort-first
  - adr-0035-jpn-seizure-cluster-topology
  - adr-2604272200-arms-firearm-id-authentication
supersedes: []
superseded_by: []
---

# ADR-2604272200: Arms firearm ID authentication system

**Date**: 2026-04-27
**Status**: Active
**Layer**: L3 CF Worker Dispatcher + L4 Kotoba/Datomic registry
**Actor DID**: `did:web:arms.etzhayyim.com`
**Complies with**: ADR-0036 (Worker-direct Hyperdrive), ADR-0018 (Tier 3 PII), ADR-0004 (Write-only Derived)

## Goal

Enable physical firearm ID authentication and immutable chain-of-custody tracking across jurisdictions, with cryptographic holder authentication, export-control enforcement, and integration with the open-defence incident cluster.

## Scope

- `arms.etzhayyim.com` CF Worker — 12 XRPC methods under `com.etzhayyim.apps.arms.*`
- Kotoba/Datomic schema: 5 vertex tables + 2 PII tables + 2 edge tables + 1 MV
- Rego AuthZ policy: `00-contracts/policies/etzhayyim/xrpc/arms/`
- Defence cluster integration: `vertex_open_defence_event`

## Decision

### D1 — DID challenge-response holder authentication

Restricted operations (`checkOutFirearm`, `transferCustody`) require a **passed auth session** in `vertex_arms_auth_session`.

Flow:
1. Caller → `authenticateHolder` → receives 32-char nonce, 5-minute TTL, `sessionId`
2. Caller signs nonce with their DID key → `verifyAuthChallenge` → session `auth_status = 'passed'`
3. Caller presents `sessionId` on restricted call → Worker validates TTL + status → proceeds

The Rego policy gate (`input.auth.holderAuthSessionPassed = true`) is the enforcement point. The Worker populates this field by querying `vertex_arms_auth_session` before routing to XRPC dispatch.

**Rationale**: AT Protocol DID keys are already the platform identity primitive. Reusing them for physical asset custody sign-off avoids a separate credential system. The 5-minute TTL matches PSD2 "dynamic linking" semantics for high-value transactions.

### D2 — Tier 3 PII split (ADR-0018 compliant)

Public tables (`vertex_arms_firearm`, `vertex_arms_permit`) store SHA-256 hashed identifiers only:
- `serial_hash` = `sha256(serialNumber)`
- `permit_hash` = `sha256(permitNumber)`

Full plaintext lives in restricted `*_pii` tables:
- `vertex_arms_firearm_pii` — serial number, make, model, caliber, country of origin, ECCN
- `vertex_arms_permit_pii` — permit number, holder name, issuing authority, jurisdiction, expiry

`getFirearm` and `getPermit` queries join PII only when caller has `arms:authority` or `arms:law-enforcement` permission set. Public holders see hashed fields only.

### D3 — Export control gate (HTTP 451)

Rego policy blocks `transferCustody` and `reportIncident` to 12 ATT/Wassenaar-restricted jurisdictions:

```
KP, IR, SY, RU, BY, MM, SD, CF, LY, SO, YE, SS
```

`deny_obligations contains "return_451"` — the Worker must return HTTP 451 (Unavailable For Legal Reasons) when this obligation fires. HTTP 451 is semantically correct per RFC 7725 §3.

The restricted list is `data.export_restricted_jurisdictions` in `00-contracts/policies/etzhayyim/xrpc/arms/data.json` — update that file, not the Rego logic, when the list changes.

### D4 — Defence cluster incident integration

`reportIncident` dual-writes:
1. `vertex_arms_custody_event` (type = `incident`) — arms domain record
2. `vertex_open_defence_event` — open-defence cluster cross-reference

This makes arms incidents visible to the open-defence actor without a separate subscription. Both writes go through `createKyselyDb(env.HYPERDRIVE)` in a single handler per ADR-0036.

### D5 — Graph schema

```
vertex_arms_firearm          (vertex_id, registered_at, status, model_code, manufacturer_did, jurisdiction, serial_hash, eccn_code)
vertex_arms_firearm_pii      (vertex_id, firearm_vid, serial_number, make, model, caliber, country_of_origin, eccn_code, encrypted_at)
vertex_arms_permit           (vertex_id, firearm_vid, holder_did, permit_type, permit_hash, issued_at, expires_at, jurisdiction, status)
vertex_arms_permit_pii       (vertex_id, permit_vid, permit_number, holder_name, issuing_authority, jurisdiction, expiry_date)
vertex_arms_auth_session     (vertex_id, holder_did, firearm_vid, challenge_nonce, auth_status, created_at, expires_at)
vertex_arms_custody_event    (vertex_id, firearm_vid, event_type, from_did, to_did, timestamp, jurisdiction, notes)
edge_arms_firearm_to_holder  (src, dst, since, permit_vid)
edge_arms_firearm_to_permit  (src, dst, permit_type, status)
mv_arms_active_by_holder     (holder_did, firearm_vid, permit_type, issued_at, expires_at, jurisdiction)
```

## XRPC Surface

| NSID | Auth | Notes |
|------|------|-------|
| `com.etzhayyim.apps.arms.registerFirearm` | `arms:system` | Internal only |
| `com.etzhayyim.apps.arms.getFirearm` | `arms:holder` or `arms:authority` | PII join gated |
| `com.etzhayyim.apps.arms.issuePermit` | `arms:authority` | |
| `com.etzhayyim.apps.arms.getPermit` | `arms:holder` or `arms:authority` | PII join gated |
| `com.etzhayyim.apps.arms.revokePermit` | `arms:authority` | |
| `com.etzhayyim.apps.arms.authenticateHolder` | public | Returns challenge nonce |
| `com.etzhayyim.apps.arms.verifyAuthChallenge` | `arms:holder` | Sets session passed |
| `com.etzhayyim.apps.arms.checkOutFirearm` | `arms:holder` + auth session | |
| `com.etzhayyim.apps.arms.checkInFirearm` | `arms:holder` | |
| `com.etzhayyim.apps.arms.transferCustody` | `arms:authority` + export gate | HTTP 451 on restricted |
| `com.etzhayyim.apps.arms.reportIncident` | `arms:holder` or `arms:authority` | Defence dual-write |
| `com.etzhayyim.apps.arms.getAuditLog` | `arms:authority` or `arms:law-enforcement` | |

## Rego AuthZ

Policy: `00-contracts/policies/etzhayyim/xrpc/arms/policy.rego`
Data: `00-contracts/policies/etzhayyim/xrpc/arms/data.json`
Tests: `00-contracts/policies/etzhayyim/xrpc/arms/test.rego` (10 cases, all passing)

Package: `etzhayyim.xrpc.arms`

Key rules:
- `internal_service` — `input.auth.method == "service-jwt"` bypasses all holder gates
- `holder_auth_session_valid` — `input.auth.holderAuthSessionPassed == true`
- `export_restricted` — destination jurisdiction in ATT/Wassenaar list
- `deny_obligations contains "return_451"` — fires on export_restricted deny
- `deny_obligations contains "return_401"` — fires on unauthenticated access

## Deployment

- Worker: `arms.etzhayyim.com` (CF Worker, `did:web:arms.etzhayyim.com`)
- nanoid: `arms`
- kotodama.jsonld: `60-apps/etzhayyim-project-arms/worker/kotodama.jsonld`
- Migration: `30-graph/graph-schema/migrations/20260427*_arms_*.ts` (9 tables applied)
- database.ts: regenerated 2026-04-27, 2,227 tables, zero drift

## Shipped Extensions

### E1 — BPMN expired-permit scanner (2026-04-28)

`arms_expired_permit_scanner` — ADR-0056 BPMN-as-actor, R/P1D timer.

- BPMN: `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/arms/expiredPermitScanner.bpmn`
- Registry migration: `30-graph/graph-schema/migrations/20260428000000_seed_arms_expired_permit_scanner.ts`
- Kotoba/Datomic rows confirmed: `vertex_bpmn_process_def` + `vertex_bpmn_lexicon_binding`
- NSID: `com.etzhayyim.apps.arms.scanExpiredPermits` (timer-start + manual trigger)
- Flow: `generic.db.select` (count active-expired) → `generic.db.insert` (PK-upsert `status='expired'`) → `generic.audit.emit`

## Pending

- `createWorkerExport()` migration: current `ExportedHandler` skips PDS actor-profile auto-registration. Low priority — arms is restricted-access, social graph visibility not required. See `deps.toml [[migrations]] arms-create-worker-export-registration`.
- `open-bis-triennial` ECCN auto-screening API integration for `registerFirearm`. See `deps.toml [[migrations]] arms-eccn-bis-triennial-screening`.

## References

- ADR-0036 Worker-direct Hyperdrive persistence
- ADR-0018 PII Tier 3 + cohort-first
- ADR-0035 JPN Seizure cluster topology (pattern reference)
- `00-contracts/policies/etzhayyim/xrpc/arms/` — Rego policy + data + tests
- `60-apps/etzhayyim-project-arms/worker/src/app.ts` — Worker implementation
- `30-graph/graph-schema/migrations/` — Kotoba/Datomic DDL
