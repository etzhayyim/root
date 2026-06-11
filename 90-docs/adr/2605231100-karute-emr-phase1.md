---
id: adr-2605231100-karute-emr-phase1
title: "ADR-2605231100: karute.etzhayyim.com — FHIR R5 EMR Phase 1"
status: proposed
doc_type: adr
topic: karute-emr-phase1
authoritative: true
last_verified: 2026-05-23
priority: 7.2
axis: architecture
weight: 0.72
priority_note: "Adds a clinical EMR actor on the etzhayyim RW-free substrate. PHI on MST is only viable via the encrypted-record envelope (ADR-2605181100), and the FHIR R5 mapping decides the lexicon shape for every downstream clinical app."
authoritative_for:
  - karute actor topology and DID
  - FHIR R5 ↔ com.etzhayyim.karute.* lexicon mapping
  - clinical PHI handling rules on etzhayyim substrate
  - encrypted-envelope vs public-meta split for clinical records
depends_on:
  - adr-2605172000-etzhayyim-rw-free-substrate
  - adr-2605181100-mst-encrypted-records-signal-keywrap
  - adr-2605172100-etzhayyim-payments-on-chain-only
  - adr-2605172400-etzhayyim-vendor-three-axis-split-rule
related:
  - adr-2605080800-iryo-hospital-ops-phase1
  - adr-2605192100-etzhayyim-mission-charter
supersedes: []
superseded_by: []
---

# ADR-2605231100: karute.etzhayyim.com — FHIR R5 EMR Phase 1

**Status**: proposed
**Date**: 2026-05-23
**Deciders**: Jun Kawasaki

# Context

`etzhayyim/root` currently has no electronic medical record (EMR / 電子カルテ) actor. The closest adjacencies — ADR-2605080800 (`iryo.etzhayyim.com:hospital`, vendor-side, DRG-oriented hospital ops), `medical-coverage-{ingester,mcp}` (PubMed / ClinicalTrials.gov ingest), `00-contracts/lexicons/com/etzhayyim/apps/fhirHealthData/` (terminology registration only) — all sit *adjacent to* the clinical encounter but none implement the **patient-centric chart**: SOAP, Rx, vitals, orders. ADR-2605181100 §1.3 names "uhl-right-neural patient referrals" as a primary driver for encrypted records, and §5.2 explicitly defers EMR consumer implementation.

Phase 1 fills that gap. Three forces shape the design:

1. **PHI confidentiality is non-negotiable.** Clinical records are 要配慮個人情報 (個保法 §2-3); the etzhayyim charter's Wellbecoming + 反個人主義 ontology raises this to a constitutional invariant. Plaintext PHI on MST is prohibited.
2. **The substrate is RW-free.** No Kotoba/Datomic, no Postgres, no fiat processor. AT MST + IPFS + Base L2 + USDC/ERC-4337. Apps that need insurance billing call `iryo.etzhayyim.com` (vendor) via consent capability.
3. **FHIR R5 is the international portability anchor.** JP DPC, US MS-DRG, EU AR-DRG all flow through FHIR R5 + ICD-10 + LOINC + SNOMED. The lexicon must be a 1:1 FHIR R5 mirror so export is mechanical and ingestion from external EHRs lands without translation loss.

# Decision

## Identity

- **DID**: `did:web:karute.etzhayyim.com`
- **Nanoid**: `karu7t3e`
- **Entrypoint**: `https://karu7t3e.etzhayyim.com/xrpc/com.etzhayyim.apps.karute.*`
- **Topology**: standalone actor (NOT `did:web:iryo.etzhayyim.com:karute`). `iryo.etzhayyim.com` is vendor-side (DPC/DRG billing, hospital ops); the etzhayyim karute actor is its peer for patient-centric clinical content. The two can call each other via consent capability when insurance billing is needed.

## Two-tier record split

| Tier | Collection | Content | Visibility |
|---|---|---|---|
| **Encrypted (PHI)** | `com.etzhayyim.encrypted.record` envelope with `innerType = com.etzhayyim.karute.*` | Patient, Encounter, SOAP, Observation, Condition, MedicationRequest, ServiceRequest | Ciphertext on PDS; readable only by holders of Signal-wrapped key-wrap |
| **Public meta** | `com.etzhayyim.apps.karute.*` collections + graph `KaruteX` nodes | rkey pointers, occurredAt, *Did refs, terminology codes (LOINC/ICD-10/RxNorm), interaction-severity-max | Plaintext for discovery / timeline / coverage stats |

Public meta MUST NOT contain: patient name, DOB, address, free-text symptom, lab values, drug strengths, diagnosis labels. It MAY contain: terminology codes (de-identified by design), DIDs (identifiers but not by themselves identifying), timestamps, status enums.

## Inner-type lexicon (FHIR R5 ↔ com.etzhayyim.karute.*)

| FHIR R5 Resource | Lexicon NSID |
|---|---|
| `Patient` | `com.etzhayyim.karute.patient` |
| `Encounter` | `com.etzhayyim.karute.encounter` |
| `Composition` (SOAP section) | `com.etzhayyim.karute.soapNote` |
| `Observation` | `com.etzhayyim.karute.observation` |
| `Condition` | `com.etzhayyim.karute.condition` |
| `MedicationRequest` | `com.etzhayyim.karute.medicationRequest` |
| `ServiceRequest` | `com.etzhayyim.karute.serviceRequest` |

Field-level FHIR drift is allowed only where (a) AT Lexicon has no float — all numerics use `{valueScaled, scale, unit}`; (b) JP-specific extensions (フリガナ, 都道府県, YJ code, JLAC10, 診療行為コード) are first-class properties rather than FHIR `extension[]`. Export to FHIR R5 Bundle does the float reconstruction + extension wrapping.

## XRPC API (13 methods)

Write procedures: `createPatient`, `createEncounter`, `createSoapNote`, `createObservation`, `createCondition`, `createMedicationRequest`, `createServiceRequest`.

Read queries: `listPatients`, `getPatient`, `listEncounters`, `listSoapNotes`, `listObservations`, `listMedications`, `listOrders`, `getChartSummary`, `exportFhirBundle`, `healthKarute`.

Write procedures take `(record, recipientDids, publicMeta)`. The pipeline encrypts `record` via `@etzhayyim/sdk.encryptedWrite`, writes ciphertext envelope to `com.etzhayyim.encrypted.record`, and writes a stripped-down `publicMeta` projection to the graph node. `createMedicationRequest` adds an upstream `agent.chat` interaction check; `shouldBlock: true` halts the write unless `overrideInteractionBlock` is set (audited via amendment record).

## Clinician role model

| Role | Capabilities |
|---|---|
| MD | full CRUD on all kinds; Rx prescriber |
| NP | create SOAP / Observation / ServiceRequest; Rx co-signer only |
| RN | create Observation (vitals, lab specimen handling) + ServiceRequest fulfillment |
| PHARM (Phase 2) | read Rx; create `dispenseRecord` (deferred) |
| ADMIN | read public meta only; no read-cap allocation |
| PATIENT | read own; `exportFhirBundle` to external EHR |

Roles are enforced at the SDK seam (`@etzhayyim/sdk` checks DID role assertions before producing a key-wrap); not at the lexicon level, because lexicons are role-agnostic data contracts.

## AI assistance scope

The pipelines invoke `agent.chat` for three specific tasks:

1. **Drug-drug / drug-allergy interaction check** on `createMedicationRequest`. Input is patient public meta (RxNorm/YJ code list, allergy code list) + proposed medication. Output flags severity tiers (minor / moderate / major / contraindicated) and a recommendation; `contraindicated` blocks by default.
2. **PHI-redacted chart summary** on `getChartSummary`. Input is the public-meta timeline (innerType, occurredAt, codes); output is a <200 word narrative containing only de-identified counts and code-system pointers. Plaintext PHI is never sent to the LLM.
3. **SOAP composition assist** (deferred to Phase 2). When the clinician writes plaintext in the browser, the SDK locally derives a structure suggestion and synchronously decrypts/re-encrypts. No PHI leaves the device.

## Substrate hard-rules (extends ADR-2605172000 + ADR-2605181100)

1. App code MUST NOT import `@noble/ciphers` / `@signalapp/libsignal-client` directly; only `@etzhayyim/sdk` is allowed.
2. App code MUST NOT write plaintext PHI to MST. Lefthook hook `karute-phi-plaintext-guard` (Phase 2 deliverable) greps the diff for `com.etzhayyim.karute.*` writes outside the encrypted envelope.
3. App code MUST NOT call `iryo.etzhayyim.com` (vendor) directly for billing unless the patient has issued a consent capability via `com.etzhayyim.consent.capability` (separate ADR, deferred).
4. Public-meta projections MUST NOT include any of: family/given name, DOB, address line, free-text symptom, lab numeric value, diagnosis display string. Allowed: code system + code (LOINC/ICD-10/RxNorm), DID, timestamp, status enum, interaction-severity-max.

## 3-axis split (ADR-2605172400) classification

| Axis | Disposition | Rationale |
|---|---|---|
| **Liability** | etzhayyim | PHI custody liability rests with patient (DID-owned read-cap) + clinician (treatment relationship). No vendor commercial liability shield required for the core substrate. Insurance-billing liability is delegated to `iryo.etzhayyim.com` (vendor) only when invoked. |
| **Custody** | etzhayyim | PDS + IPFS self-hosted; encrypted at rest; key custody = patient + clinician DIDs. No vendor data-controller role. |
| **Settlement** | etzhayyim | Self-pay clinics use USDC + ERC-4337 (etzhayyim primitive). Insurance settlement is delegated through consent capability — not an etzhayyim concern. |

All three axes resolve to etzhayyim → `etzhayyim/root` is the correct home.

# Consequences

## 正の効果

- **Constitutional PHI safety.** Ciphertext on the substrate; verifier-from-outside property of MST + L2 anchor preserved; audit-without-reading supported (regulator can prove a record existed at L2 block N without reading it).
- **FHIR R5 portability.** Patient can `exportFhirBundle` to any external EHR. The reverse path (import from external EHR) lands by reading `application/fhir+json` and writing through the same `create*` procedures.
- **AI assistance without PHI exfiltration.** LLM only ever sees de-identified codes; this is structurally enforced by which collection the agent reads from.
- **Patient as DID-first principal.** The patient DID is the canonical identity, owns its read-cap, and is the export endpoint — aligns with `did:plc`/`did:web` substrate ergonomics rather than fighting them.

## 負の効果 / コスト

- **No PHI search on the substrate.** Free-text search of clinical notes requires client-side decryption + local index, or a separate consent-bound search service. Phase 1 punts: list/filter is by code + timestamp only.
- **Interaction check requires up-to-date public meta.** Allergies and active medication list must be queryable via public meta (or via patient-bundled disclosure to the prescribing clinician). Phase 1 surfaces RxNorm/YJ codes + allergy code list in public meta — these are codes, not PHI in the strict sense, but they leak the *fact* that the patient is on medication X.
- **No insurance billing in Phase 1.** Self-pay clinics work day one; insurance-billing clinics need the consent-capability ADR + `iryo.etzhayyim.com` integration first.
- **Key-wrap fan-out per record.** Every record carries N key-wrap records (one per recipient: patient, attending MD, attending NP, RN, etc.). Group-rekey on team change is manual (re-encrypt and re-wrap to remaining members). ADR-2605181100 §5.4 already names this as substrate-wide cost.
- **No PCS for data at rest.** A leaked record key reveals all past records under that key. Mitigation: per-encounter rekey + tombstone on member removal (deferred operational protocol).
- **AT Lexicon has no float.** Every numeric in clinical records (BP, temperature, drug strength, lab value) uses `{valueScaled, scale, unit}`. Round-trip with FHIR R5 requires explicit scale reconstruction in export.

## Rollout

1. **This commit** — Actor manifest + 7 inner-type lexicons + 13 XRPC lexicons + ADR + Svelte SuperApp UI scaffold.
2. **Next: SDK seam + Phase 1 pipelines** — `@etzhayyim/sdk` `encryptedWrite` / `encryptedRead` need karute-specific tightenings (recipient role enforcement, public-meta projector). Pipeline implementation lives in `40-engine/kotoba/crates/kotoba-kotodama/cells/` (Pregel cells), not the actor manifest itself.
3. **Then: lefthook `karute-phi-plaintext-guard`** — diff-grep that blocks any plaintext PHI write.
4. **Phase 2** — pharmacy dispense flow, consent-capability ADR + iryo billing bridge, SOAP-assist on-device LLM, patient portal (read-only).
5. **Phase 3** — 在宅医療 (home care) episode, telehealth video, second-opinion marketplace.

# Alternatives Considered

## A. Extend `iryo.etzhayyim.com:karute` path-based topology

The Phase 1 iryo ADR (2605080800) sketches `:hospital` / `:clinic` / `:zaitaku`, suggesting `:karute` would follow naturally. Rejected because iryo is vendor-side (Kotoba/Datomic + Stripe + DRG billing): putting patient-centric chart there means PHI lives in a substrate that the etzhayyim charter prohibits for confidential records. The two actors can interoperate (consent capability), but they belong in different repos for the same 3-axis reason that splits them at all.

## B. Single-tier (no public meta, everything in encrypted envelope)

Cleaner privacy story (zero metadata leak on MST beyond CID + ciphertext size + write timestamp). Rejected because **discovery requires public meta**: a clinician must be able to list "today's encounters" or "active medications" without first negotiating a read-cap with every patient. The current design exposes the *codes* (LOINC, ICD-10, RxNorm) which are deliberately de-identified vocabularies. It does leak the cardinality and timing of clinical events for each patient DID — flagged in ADR-2605181100 §5 "metadata leakage that this design does not solve"; follow-up ADR on rkey blinding + padding remains the mitigation path.

## C. FHIR R5 with extensions instead of native JP fields

Keep `com.etzhayyim.karute.patient` minimal FHIR; push フリガナ, 都道府県, YJ code, JLAC10 into FHIR `extension[]`. Rejected because in practice every JP clinic queries those fields constantly (intake screens, formulary lookup); making them extensions buries them behind extra path traversal in every consumer. Export to canonical FHIR still wraps them into `extension[]`, so the wire format remains FHIR-compatible.

## D. ICD-11 instead of ICD-10

ICD-11 launched 2022; some JP institutions are migrating. Rejected for Phase 1 because (i) JP DPC + national health insurance still bill in ICD-10-JP, (ii) most existing EHR exports speak ICD-10. The lexicon allows ICD-10 + SNOMED CT (which is ICD-11-aligned) side-by-side; ICD-11 can be added as an additional code system on `condition.code` without lexicon migration.

## E. Use `hc` actor (existing) for medical task workflow

The `hc` (Human Computing) actor handles gig/microtask flows and could in principle host "physician visit task" pipelines. Rejected because (i) the hc lexicon shape is fundamentally task/shift/booking, not clinical resource, (ii) hc's billing path (USDC/USDT escrow) doesn't model fee-for-service medicine, (iii) clinical PHI handling deserves its own actor for compliance audit isolation.

# References

- ADR-2605172000 [etzhayyim RW-free substrate](./2605172000-etzhayyim-rw-free-substrate.md)
- ADR-2605181100 [MST encrypted records + Signal key-wrap](./2605181100-mst-encrypted-records-signal-keywrap.md) — the confidentiality layer this ADR consumes
- ADR-2605172100 [etzhayyim payments on-chain only](./2605172100-etzhayyim-payments-on-chain-only.md)
- ADR-2605172400 [etzhayyim/vendor 3-axis split rule](./2605172400-etzhayyim-vendor-three-axis-split-rule.md)
- ADR-2605080800 [iryo.etzhayyim.com hospital ops Phase 1](https://github.com/etzhayyimcojp/etzhayyim-apps-etzhayyimcojp/blob/main/90-docs/adr/2605080800-iryo-hospital-ops-phase1.md) — vendor-side peer for billing
- ADR-2605192100 [etzhayyim mission charter](./2605192100-etzhayyim-mission-charter.md) — Wellbecoming + 反個人主義 grounds for PHI confidentiality
- HL7 FHIR R5 — https://hl7.org/fhir/R5/
- LOINC — https://loinc.org/
- ICD-10-JP — 厚生労働省 疾病、傷害及び死因の統計分類
- SNOMED CT — https://www.snomed.org/
- RxNorm — https://www.nlm.nih.gov/research/umls/rxnorm/
- JLAC10 (日本臨床検査医学会) — http://www.jslm.org/committees/code/index.html
