---
id: adr-2604280000-telecom-tmf-esim-phases17-18
title: "ADR-2604280000: Telecom Phase 17 (TM Forum Open APIs) + Phase 18 (eSIM/eUICC Lifecycle)"
status: active
doc_type: adr
topic: telecom-bss-esim
authoritative: true
last_verified: 2026-04-28
authoritative_for:
  - telecom-tmf-open-api-flows
  - telecom-esim-lifecycle-bpmn
related:
  - adr-0056-bpmn-as-actor
  - adr-0018-pii-tier3-cohort-first
---

# ADR-2604280000: Telecom Phase 17 (TM Forum Open APIs) + Phase 18 (eSIM/eUICC Lifecycle)

**Date**: 2026-04-28
**Status**: Active
**Supersedes**: —
**Relates to**: ADR-0056 (BPMN-as-actor), ADR-0018 (PII Tier 3)

---

## Context

Telecom carrier actor (`did:web:telecom.etzhayyim.com`) reached phases 1–16 across prior sessions.
This ADR documents the final two phases of the initial 18-phase MNO/MVNO actor build.

**Phase 17 — TM Forum Open APIs (TMF 620/622/637/641/640/638/666/678)**
The BSS/OSS layer is incomplete without a product/service catalog and customer billing surface.
Eight TMF NGOSS Open API process flows are needed to close the end-to-end quote-to-cash loop:
catalog → order → inventory on both product and service axes, plus account management and bill issuance.

**Phase 18 — eSIM / eUICC Lifecycle (GSMA SGP.22 Consumer + SGP.02 M2M)**
eSIM provisioning is now the dominant SIM issuance path. The full GSMA SGP.22 lifecycle
(EID provisioning, SM-DP+ profile download/enable/disable/delete, SM-DS event registration,
state auditing, and MNO-to-MNO ownership transfer) requires dedicated BPMN actors and
graph schema. EID and ICCID are quasi-PII (device-bound) and are stored sha256: hashed.

---

## Decision

### Phase 17 — TM Forum Open APIs

8 BPMN actors + lexicons registered via ADR-0056:

| BPMN process ID | NSID | Standard |
|---|---|---|
| `telecom_publish_product_offering` | `com.etzhayyim.apps.telecom.publishProductOffering` | TMF620 |
| `telecom_submit_product_order` | `com.etzhayyim.apps.telecom.submitProductOrder` | TMF622 |
| `telecom_record_product_inventory_item` | `com.etzhayyim.apps.telecom.recordProductInventoryItem` | TMF637 |
| `telecom_submit_service_order` | `com.etzhayyim.apps.telecom.submitServiceOrder` | TMF641 |
| `telecom_activate_service_instance` | `com.etzhayyim.apps.telecom.activateServiceInstance` | TMF640 |
| `telecom_record_service_inventory_item` | `com.etzhayyim.apps.telecom.recordServiceInventoryItem` | TMF638 |
| `telecom_register_customer_account` | `com.etzhayyim.apps.telecom.registerCustomerAccount` | TMF666 |
| `telecom_issue_customer_bill` | `com.etzhayyim.apps.telecom.issueCustomerBill` | TMF678 |

Graph schema (`20260427220000_vertex_telecom_tmf.ts`): 8 vertex tables + 3 edge tables + 6 MVs.
PII discipline: `partyName`/`partyContact`/`partyTaxId`/`billingAddress` described as sha256: hashed
in lexicon; timer-start `R/P1M` for `issueCustomerBill`.

pyzeebe primitive: `pymagatama.primitives.telecom_tmf` (8 task handlers).

### Phase 18 — eSIM/eUICC Lifecycle (GSMA SGP.22)

8 BPMN actors + lexicons registered via ADR-0056:

| BPMN process ID | NSID | SGP.22 operation |
|---|---|---|
| `telecom_provision_euicc` | `com.etzhayyim.apps.telecom.provisionEuicc` | EID registration |
| `telecom_download_esim_profile` | `com.etzhayyim.apps.telecom.downloadEsimProfile` | SM-DP+ profile download |
| `telecom_enable_esim_profile` | `com.etzhayyim.apps.telecom.enableEsimProfile` | Enable profile |
| `telecom_disable_esim_profile` | `com.etzhayyim.apps.telecom.disableEsimProfile` | Disable profile |
| `telecom_delete_esim_profile` | `com.etzhayyim.apps.telecom.deleteEsimProfile` | Delete profile |
| `telecom_register_smdp_event` | `com.etzhayyim.apps.telecom.registerSmdpEvent` | SM-DS event registration |
| `telecom_audit_euicc_state` | `com.etzhayyim.apps.telecom.auditEuiccState` | eUICC state audit (timer R/PT4H) |
| `telecom_transfer_esim_ownership` | `com.etzhayyim.apps.telecom.transferEsimOwnership` | MNO-to-MNO porting (SGP.22 Annex H) |

Graph schema (`20260427230000_vertex_telecom_esim.ts`): 6 vertex tables + 2 edge tables + 3 MVs.
PII discipline: EID stored as `sha256:` hashed (device-bound quasi-PII); ICCID stored as
`sha256:` hashed. `sensitivity_ord=2`. No full PII in the graph layer.

pyzeebe primitive: `pymagatama.primitives.telecom_esim` — `_hash()` helper enforces
`sha256:` prefix before any persistence; accepts pre-hashed values transparently.

---

## Verification

```
bpmn-coverage:     OK (216 bindings; telecom=142)
bpmn-structural:   OK (216 BPMN files parsed)
Kotoba/Datomic P17:    8/8 vertex_bpmn_lexicon_binding rows active (actor_id=sys.bpmn.seed.telecom-tmf)
Kotoba/Datomic P18:    8/8 vertex_bpmn_lexicon_binding rows active (actor_id=sys.bpmn.seed.telecom-esim)
```

---

## Consequences

- Total telecom BPMN actors: **142** across 18 phases
- New pyzeebe modules registered: `telecom_tmf`, `telecom_esim`
- BSS quote-to-cash loop closed: product catalog → order → inventory → account → bill
- eSIM full lifecycle covered: provisioning → profile ops → SM-DS → audit → MNO transfer
- Remaining deferred scope: MEC/EAS, NPN, SDN-NFV, WBA OpenRoaming, oneM2M IoT, 6G research,
  quantum-safe migration (see telecom project entry `Phase 10 deferred`)
