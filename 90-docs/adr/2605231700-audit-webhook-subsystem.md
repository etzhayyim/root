---
id: adr-2605231700-audit-webhook-subsystem
title: "ADR-2605231700: Audit webhook subsystem (constitutional observability)"
status: proposed
doc_type: adr
topic: audit-webhook-subsystem
authoritative: true
last_verified: 2026-05-23
priority: 7.0
axis: architecture
weight: 0.70
priority_note: "Closes the consent-capability observability gap from ADR-2605231400 §'Revocation semantics'. Provides a typed, signed, hash-chained, PHI-free event stream that the patient (or a delegated auditor) can subscribe to in order to detect honor failures by grantees (clinicians / vendor iryo / external EHRs)."
authoritative_for:
  - "audit event record shape (`com.etzhayyim.audit.event`)"
  - "emission rules — which substrate operations emit events"
  - "hash-chain semantics for audit log integrity"
  - "auditor-subscription pattern"
depends_on:
  - adr-2605181100-mst-encrypted-records-signal-keywrap
  - adr-2605231100-karute-emr-phase1
  - adr-2605231400-karute-consent-capability-iryo-bridge
  - adr-2605231603-per-record-rekey-tombstone-protocol
related:
  - adr-2605172000-etzhayyim-kotoba-substrate
supersedes: []
superseded_by: []
---

# ADR-2605231700: Audit webhook subsystem

**Status**: proposed
**Date**: 2026-05-23
**Deciders**: Jun Kawasaki

# Context

ADR-2605231400 §"Revocation semantics" stated:

> Auditor webhooks (`constraints.auditWebhookDid`) receive both invocation and revocation events, providing a public timeline a regulator can subpoena.

ADR-2605231603 §"Audit emission" stated:

> Every tombstone with non-empty `auditWebhookDids` triggers an `com.etzhayyim.audit.event` per webhook target.

Both ADRs deferred the actual event format and delivery mechanism. This ADR specifies them.

The forces:

- **Patient sovereignty**: a patient who issued a consent capability MUST be able to detect that the grantee actually invoked it, against which records, at which time.
- **Charter §1.12 transparency**: religious-corp force / governance operations require transparent on-chain log; the same property must extend to PHI-adjacent operations (consent invocation, tombstone events).
- **No PHI in audit events**: events must reference CIDs and DIDs, never plaintext clinical content. This is what makes events safe to publish in a patient's audit PDS subject (which may itself have looser read-cap policy than the clinical records).
- **Integrity under untrusted aggregator**: the auditor subject (delegate DID) might be operated by a third party. The event chain MUST be verifiable independently of the aggregator's honesty.

# Decision

## Event shape

`com.etzhayyim.audit.event` (the lexicon shipping with this ADR). Required fields: `eventType`, `subjectDid`, `actorDid`, `occurredAt`, `signature`. The signature is over the canonicalized payload by the **actor** (not the auditor) — the audit record is the actor's own attestation, mirrored to the subject's audit PDS.

The 13 `eventType` values cover:

- consent: `granted` / `revoked` / `invoked` / `expired`
- encrypted: `write` / `read` / `keyWrap.issued` / `keyWrap.refused`
- tombstone: `rekey` / `redact` / `sealed`
- billing: `requested` / `claim.statusChanged`
- PHI guard: `phi.guard.violation` (lint-blocked write attempts that escaped via inline bypass)

## Hash chain

Each event includes `auditChainPrev` pointing to the prior `audit.event` CID from the **same actor in the same audit subject's PDS**. This forms a per-(actor, subject) hash chain. Verifiers walk the chain to detect omissions: a missing event is detectable because the next event's `auditChainPrev` would point to a CID the verifier didn't see.

The chain DOES NOT prevent insertion — an actor could write events that didn't actually happen (false positives). It DOES prevent silent omission (false negatives) within a chain segment.

## Subject vs actor PDS

Events are written to **the subject's audit PDS** (`subjectDid` is typically the patient). The actor signs the event with their own key. This creates:

- One canonical timeline per patient.
- Cross-actor visibility: the patient's PDS shows events from every clinician / agent / vendor that touched their data.
- Trust split: the actor proves "I did this"; the subject's PDS proves "this is the order in which things were written to my view."

If `auditWebhookDid` is set on a capability or tombstone, an additional copy is written to that DID's PDS — supporting delegate-auditor patterns (e.g. a clinician-licensure board subscribes to events about a specific clinician).

## Emission rules

| Operation | Always emits | Emits when configured |
|---|---|---|
| `grantConsent` | ✓ (`consent.granted`) | — |
| `revokeConsent` | ✓ (`consent.revoked`) | — |
| `requestIryoBilling` | ✓ (`consent.invoked` + `billing.requested`) | — |
| iryo claim status change | ✓ (`billing.claim.statusChanged`) | — |
| Consent capability auto-expiry | ✓ (`consent.expired`) | — |
| `encryptedWrite` of `com.etzhayyim.karute.*` | — | When `constraints.auditWebhookDid` set on a covering capability, OR the patient has opted in globally via `karute.setAuditPolicy` (Phase 2). |
| `encryptedRead` by non-self actor | — | Same as above. |
| `keyWrap.issued` to grantee | ✓ (in subject's PDS) | — |
| `keyWrap.refused` (e.g. capability invalid) | ✓ (`outcome='denied'`) | — |
| Tombstone write (any kind) | ✓ (`tombstone.{rekey,redact,sealed}`) | — |
| PHI guard pre-commit bypass | — | When the inline `// phi-guard: allow` comment is detected — a server-side log shadow-writes a `phi.guard.violation` event for transparency. Phase 2. |

## Failure modes

- **Audit write fails**: the underlying operation MUST NOT silently succeed. The actor's pipeline retries with exponential backoff; if all retries fail, the operation rolls back (where possible) and surfaces an error to the caller. For irreversible operations (already-committed envelope), the actor writes a `phi.guard.violation` event with `outcome='error'` at next opportunity.
- **Audit chain gap detected by verifier**: the verifier raises a `chain-gap` finding. Resolution requires the actor to publish the missing events or explain (likely a service interruption; not necessarily malicious).
- **Audit subject's PDS unavailable**: emission is queued at the actor's substrate. Once the subject's PDS returns, the queued events are flushed in order.

## UI integration

`PatientPortalView.svelte` gains an "Audit log" section that subscribes to `subscribeRepos` on the patient's own `com.etzhayyim.audit.event` collection (or polls via `karute.listAuditEvents`). Each event renders with:

- 🔵 consent events — issued, invoked, expired, revoked
- 🟢 read/write — when grantees decrypt records
- 🟠 tombstone — rekey/redact/sealed operations
- 🔴 violation — denied operations, guard bypasses

## What this ADR does NOT change

- The encryption envelope is untouched — events reference envelope CIDs and don't carry plaintext.
- The consent capability primitive is unchanged — this ADR specifies how the `auditWebhookDids` field's events are formatted.
- The substrate boundary is preserved — events live on AT MST like every other record.

# Consequences

## 正の効果

- **Patient observability**: revocation honor failure is detectable. If `revokeConsent` fires but the grantee continues `encryptedRead`, a `consent.invoked` event after the revoke timestamp surfaces the violation.
- **Charter §1.12 transparency** extended to PHI-adjacent operations. Force is not the only domain that benefits from on-chain audit; medical disclosure does too.
- **Cross-actor accountability**: each clinician, agent, vendor that touches a patient's data leaves a signed trace. A clinician licensure board can pull the patient's audit collection and reconstruct activity.
- **Composes with consent**: same primitive serves capability-scoped auditing AND substrate-wide observability.
- **PHI-free by design**: audit events are safely public (within the subject's PDS scope).

## 負の効果 / コスト

- **Emission volume**: every consent grant + invocation + revocation + tombstone + keyWrap operation writes an event. At ~10 events per encounter × hundreds of encounters per day per clinic, this is ~10⁴ events/day per clinic. AT Protocol MST cost is small but not zero.
- **Hash-chain insertion attacks**: an actor can write false-positive events. Mitigation: each event is signed by the actor; verifier can ignore events not signed by the operation's nominal actor.
- **Patient-PDS write requires keyWrap-like authorization**: the subject's PDS must accept writes from arbitrary actors (signed). Phase 2 adds a per-subject acceptance policy: subject can declare allowlist DIDs whose events they accept.
- **Aggregator-driven omission**: if the subject's PDS itself drops events, the chain detects the gap but the subject must trust the chain reconstruction. Mitigation: the subject can opt into a third-party auditor (e.g. clinician licensure board) which receives a mirrored copy.
- **No private audit channel**: this ADR's events are public-within-the-subject's-PDS. Consent-aware redaction (e.g., hiding event details from non-authorized viewers) is a deferred Phase 3 feature.

## Rollout

1. **This commit** — Lexicons (`audit.event` + `listAuditEvents` query) + ADR + karute pipeline emissions for grant/revoke/invoke/requestIryoBilling/rekey/redact + UI hook stub in PatientPortalView (deferred — placeholder card).
2. **Phase 2** — `setAuditPolicy` XRPC (per-subject opt-in for read/write event emission). `phi.guard.violation` shadow-write on inline bypass detection.
3. **Phase 3** — `subscribeRepos`-driven realtime audit feed in PatientPortalView. Third-party auditor mirror pattern.
4. **Phase 4** — Audit-aware redaction (events visible to consent capability holders only, for high-sensitivity subjects).

# Alternatives Considered

## A. Email/webhook out-of-band notification

Conventional pattern. Rejected because (i) email is non-public and non-anchorable, (ii) introduces a non-substrate trust point (mail server), (iii) defeats the constitutional invariant of substrate-verifiability.

## B. L2 anchor each event individually

Anchor every event to Base L2. Rejected because gas cost is prohibitive at 10⁴ events/day (≈ $30k/day at current gas). The MST + L2-anchor-of-MST-root pattern (ADR-2605172000) already gives us monotonic timeline anchoring; per-event L2 is overkill.

## C. Centralized audit service

Run a centralized audit aggregator. Rejected: re-introduces the centralized trust point ADR-2605172000 eliminated.

## D. Implicit emission via PDS firehose

Don't write explicit events; rely on the PDS subscribeRepos firehose for everything. Rejected because (i) the firehose carries plaintext records — for PHI domains this would leak metadata more aggressively than the audit.event shape, (ii) the firehose doesn't have a `subjectDid` filter natively — every consumer would need to scan all activity to find their relevant events.

## E. SIEM-style aggregation in karute's actor

Have karute's actor maintain a per-patient `auditTimeline` field. Rejected because (i) puts trust in karute as aggregator, (ii) doesn't compose across actors (a non-karute actor like iryo would write its own incompatible aggregation), (iii) the canonical "patient's view of activity on their data" should live in the patient's own PDS.

# References

- ADR-2605231400 [karute consent capability + iryo billing bridge](./2605231400-karute-consent-capability-iryo-bridge.md) §"Revocation semantics"
- ADR-2605231603 [per-record rekey + tombstone protocol](./2605231603-per-record-rekey-tombstone-protocol.md) §"Audit emission"
- ADR-2605181100 [MST encrypted records + Signal key-wrap](./2605181100-mst-encrypted-records-signal-keywrap.md)
- ADR-2605192100 [etzhayyim mission charter](./2605192100-etzhayyim-mission-charter.md) §1.12 (transparency invariant)
- 個人情報保護法 §25 (記録の保存・開示)
- HIPAA §164.312(b) (Audit controls) — comparable US framework
- SCITT (Supply Chain Integrity, Transparency, and Trust) — https://datatracker.ietf.org/wg/scitt/about/ (hash-chain integrity analogue)
