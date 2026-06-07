---
id: 260319-kotodama-wit-dodaf-nist-coverage
title: App WIT — DoDAF v2 / NIST CSF 2.0 Coverage Map
status: active
doc_type: reference
topic: wit-coverage
authoritative: true
last_verified: 2026-03-20
authoritative_for:
  - kotodama wit package coverage and compliance mapping
related:
  - 260320-kotodama-cloudflare-containers-evaluation
supersedes: []
superseded_by: []
---

# App WIT — DoDAF v2 / NIST CSF 2.0 Coverage Map

Date: 2026-03-19
Status: Authoritative
Authority: `00-contracts/wit/` (唯一の authoritative WIT source)
Note: `kotodama:dm2@1.0.0` が performer/person/organization/system/service の canonical topology。`etzhayyim:actor@0.2.0` は deprecated (`kotodama:agent@1.0.0` に吸収済み)。`etzhayyim:*@0.1.0` は orphaned。

## WIT Package Overview

| Package | Interfaces | DoDAF | NIST CSF 2.0 |
|---|---|---|---|
| `kotodama:agent@1.0.0` | agent, identity, capability, governance, dependency, skill, traceability | CV-1/2/3, SV-5, StdV-1/2, DIV-1/2 | GV, PR-AC, PR-DS, GV.SC |
| `kotodama:dm2@1.0.0` | types, performer, person, organization, system, service | AV-2, OV-4, CV-4, PV-1, SV-1/2 | GOV, ID.AM, PR-AC |
| `kotodama:core@1.0.0` | log, outbound-http, config, cypher, vector-search, remote-call, serve, resilience | SV-1, SV-4, SV-6 | PR-PT |
| `kotodama:auth@1.0.0` | passkey, authn, authz, crypto | — | PR-AC |
| `kotodama:messaging@1.0.0` | signal, signal-session, conversation, smtp, w-protocol | OV-2 | PR-DP |
| `kotodama:observability@1.0.0` | telemetry, access-log, ocel, secrets, audit-trail, anomaly, incident。`pubsub` は `[DESIGN]` (world.wit 未 import) | OV-6c, SV-7, SV-10c | DE, RS, RC, GV |
| `kotodama:workflow@1.0.0` | timer, actor-state, reminder, workflow, activity, activity-parallel, lock, virtual-actor | OV-5a/5b, OV-6b | — |
| `kotodama:storage@1.0.0` | ipfs, storage, cdn, static-site | — | — |
| `kotodama:div@1.0.0` | information, documents, materiel | DIV-3 | PR-DS |
| `kotodama:forms@1.0.0` | forms, bpmn, dmn — 全て `[DESIGN]` (world.wit 未 import) | — | — |
| `kotodama:wproto@1.0.0` (actor visibility) | follow-request, actor-sensitivity, resolve-visibility | OV-4, OV-6a, SV-10a | GV.RM-1, PR-AC-1/3/5, PR-DS-1/3, DE.AE-1 |

## Guest SDK Coverage

Date: 2026-03-20
Scope: `00-contracts/wit/world.wit` `kotodama-component`

| SDK | Import Coverage | Export Coverage | Notes |
|---|---:|---:|---|
| `kotodama-go` | 57/57 | 3/3 | historical guest SDK (removed, TS native is default) |
| `kotodama-guest-rust` | 57/57 | 3/3 | `wit_bindgen::generate!` for full world |
| `kotodama-ts` | 57/57 | 3/3 | TS native bindings (default) + `serve` (etzhayyim:serve/serve) export stub + Deno coverage tests |

### kotodama-ts Package Breakdown

| Package | Interfaces | Coverage |
|---|---:|---:|
| `kotodama:core` | 7 | 7/7 |
| `kotodama:auth` | 4 | 4/4 |
| `kotodama:messaging` | 5 | 5/5 |
| `kotodama:storage` | 4 | 4/4 |
| `kotodama:agent` | 9 | 9/9 |
| `kotodama:dm2` | 6 | 6/6 |
| `kotodama:workflow` | 8 | 8/8 |
| `kotodama:observability` | 8 | 8/8 |
| `kotodama:forms` | 3 | 0/3 (`[DESIGN]`, world.wit 未 import) |
| `kotodama:browser` | 3 | 3/3 |

### Verification

- `40-engine/kotoba/crates/kotoba-kotodama/kotodama-ts/test/wit-coverage.test.ts` asserts that every `world.wit` import is mirrored in `src/imports.ts`.
- `40-engine/kotoba/crates/kotoba-kotodama/kotodama-ts/test/wit-coverage.test.ts` asserts that every `world.wit` export is mirrored in `src/mod.ts`.
- `40-engine/kotoba/crates/kotoba-kotodama/kotodama-ts/test/cypher-helpers.test.ts` covers the TypeScript Cypher encoding/decoding helpers, including `query-json`.
- `40-engine/kotoba/crates/kotoba-kotodama/kotodama-ts/src/cbor.ts` + `src/remote.ts` provide CBOR-first typed remote-call/serve helpers with JSON fallback for legacy payloads.

## DoDAF v2 Viewpoint Coverage

| Viewpoint | WIT Interface | Coverage |
|---|---|---|
| AV-1 All View Overview | capability.discover + governance.list-standards | 90% |
| AV-2 Integrated Dictionary | dm2.types + governance.declare-entity/declare-field | 95% |
| CV-1 Capability Vision | capability.declare (capability-decl record) | 100% |
| CV-2 Capability Dependencies | capability.add-dependency (dep-type: requires/enables/enhances/conflicts) | 100% |
| CV-3 Capability Phasing | capability-phase enum (current/near-term/mid-term/far-term) | 100% |
| CV-4 Capability→Activity | capability-decl.activity-ids + traceability | 95% |
| CV-5 Capability→Services | dependency + host auto-discovery | 90% |
| CV-6 Capability→Resources | governance.data-classification | 85% |
| CV-7 Capability→Standards | governance.declare-standard | 95% |
| OV-1 Operational Concept | identity.actor-card + capability | 85% |
| OV-2 Resource Flow | w-protocol + dependency | 80% |
| OV-3 Resource Flow Matrix | dependency.check-all + host auto-discovery | 80% |
| OV-4 Performer Relationships | dm2.performer + dm2.organization (parent-child, sibling, lineage) | 95% |
| PV-1 Project Relationships | dm2.organization.list-dependencies + governance.register-manifest | 90% |
| OV-5a Activity Hierarchy | workflow.workflow + activity | 85% |
| OV-5b Activity Model | workflow.activity + traceability | 90% |
| OV-6a Operational Rules | governance.register-manifest | 85% |
| OV-6b State Transitions | workflow.workflow (status enum) | 85% |
| OV-6c Event-Trace | ocel.emit-event + audit-trail | 95% |
| SV-1 Systems Interface | dm2.system + remote-call + resilience.health-check | 90% |
| SV-2 Systems Communication | dm2.service + w-protocol + signal + remote-call | 90% |
| SV-4 Systems Functionality | WIT interface definitions + skill | 90% |
| SV-5 Activity↔Function | traceability (bidirectional) | 95% |
| SV-6 Resource Flow Matrix | dependency.check-all + resilience | 85% |
| SV-7 Systems Measures | telemetry + anomaly | 90% |
| SV-8 Systems Evolution | W Protocol social evolution + governance.standard-phase | 85% |
| SV-9 Technology Forecast | governance.declare-standard (phase: evaluating→adopting) | 85% |
| SV-10a Systems Rules | governance.check-policy + resilience.breaker | 90% |
| SV-10b State Transitions | incident.incident-status enum | 90% |
| SV-10c Event-Trace | audit-trail.emit/query | 95% |
| DIV-1 Conceptual Data | governance.declare-entity + dm2.organization | 95% |
| DIV-2 Logical Data | governance.declare-field (field-type/cardinality/ref-entity) + dm2.person | 95% |
| DIV-3 Physical Data | div.information + div.documents + div.materiel (Cypher graph) | 95% |
| StdV-1 Standards Profile | governance.declare-standard | 100% |
| StdV-2 Standards Forecast | governance.standard-phase + target-date | 100% |

## NIST CSF 2.0 Function Coverage

| Function | Subcategory | WIT Interface | Coverage |
|---|---|---|---|
| GOVERN | GV.RM-1 Governance Process | governance.register-manifest + check-policy | 90% |
| | GV.RM-2 Risk Assessment | governance.declare-risk (probability/impact/MITRE ATT&CK) | 90% |
| | GV.RM-3 Risk Treatment | governance.list-risks (status: open→mitigating→resolved) | 85% |
| | GV.SC-1 Supply Chain | governance.declare-vendor (risk-level/certifications/data-residency) | 90% |
| | GV.SC-2 Contract Management | governance.supply-chain-entry.contract-expires | 85% |
| | GV Evidence | audit-trail.emit/query | 95% |
| IDENTIFY | ID.AM-1 Asset Inventory | identity.actor-card + capability.list-own | 90% |
| | ID.AM-2 Asset Ownership | governance.role-def + identity.service-user-id | 85% |
| | ID.RA-1 Risk Assessment | telemetry + access-log (baseline) | 85% |
| | ID.RA-2 Threat Identification | governance.risk-item.mitre-id | 85% |
| PROTECT | PR-AC-1 Identities | auth.passkey + auth.authn | 90% |
| | PR-AC-3 Access Enforcement | auth.authz + governance.check-permission | 90% |
| | PR-AC-5 Credentials | secrets.get/set | 90% |
| | PR-DS-1 Data Classification | governance.classify-data (sensitivity enum) | 90% |
| | PR-DS-3 Data Minimization | governance.data-classification.pii | 85% |
| | PR-DS-4 Retention | governance.data-classification.retention-days | 90% |
| | PR-DP-1 Encryption | signal (E2E), crypto | 90% |
| | PR-DP-2 Data Integrity | MDAG commit chain (Blake3) | 90% |
| | PR-PT-1 Recovery | workflow.workflow (durable) | 85% |
| | PR-PT-2 Resilience | resilience.circuit-breaker + health-check | 90% |
| | PR-PT-3 Change Control | audit-trail (config-change category) | 90% |
| DETECT | DE.AE-1 Monitoring | telemetry + access-log | 90% |
| | DE.AE-2 Analysis | access-log.list-query-stats | 85% |
| | DE.AE-3 Event Detection | ocel.emit-event | 90% |
| | DE.AE-4 Anomaly Detection | anomaly.threshold-rule + alerts | 95% |
| RESPOND | RS.AN-1 Incident Analysis | incident.get-incident + audit-trail.query | 90% |
| | RS.AN-2 Response Process | incident.update-incident (status lifecycle) | 90% |
| | RS.MI-1 Mitigation | incident.declare-incident + workflow | 90% |
| | RS Escalation | incident.incident-sla.escalation-minutes | 85% |
| | RS Runbook | incident.incident-record.runbook-ref | 85% |
| RECOVER | RC.IM-1 Recovery Plan | incident.check-sla (RTO enforcement) | 90% |
| | RC.IM-2 Recovery Communication | w-protocol + conversation | 90% |
| | RC Postmortem | incident.incident-status.postmortem + root-cause | 90% |
