---
id: adr-2605231603-per-record-rekey-tombstone-protocol
title: "ADR-2605231603: Per-record rekey + tombstone protocol"
status: proposed
doc_type: adr
topic: per-record-rekey-tombstone-protocol
authoritative: true
last_verified: 2026-05-23
priority: 7.4
axis: architecture
weight: 0.74
priority_note: "Closes ADR-2605181100 §5.4 (deferred forward-secrecy follow-up) + §5.3 (group rekey on member removal). Defines the operational protocol for rotating record-level symmetric keys, logical-deleting records on an append-only substrate, and binding the prior/successor envelope chain so verifiers from outside can reconstruct the 'logical present' view."
authoritative_for:
  - "tombstone record shape (`com.etzhayyim.encrypted.tombstone`)"
  - "rekey / redact / sealed semantics on AT MST"
  - "group-rekey-on-removal protocol"
  - "consent-revocation-flush handler"
depends_on:
  - adr-2605181100-mst-encrypted-records-signal-keywrap
  - adr-2605231100-karute-emr-phase1
  - adr-2605231400-karute-consent-capability-iryo-bridge
related:
  - adr-2605172000-etzhayyim-kotoba-substrate
supersedes: []
superseded_by: []
---

# ADR-2605231603: Per-record rekey + tombstone protocol

> **Note (2026-05-23):** ADR-ID renumbered from 2605231600 → 2605231603 to resolve collision with the concurrently-landed `2605231600-open-seiyaku-mcp-integration.md`. Topic + content unchanged.

**Status**: proposed
**Date**: 2026-05-23
**Deciders**: Jun Kawasaki

# Context

ADR-2605181100 §5 left two open issues:

- §5.3 **Group rekey on member removal** — when a recipient is removed (e.g. care team change, consent revocation), the operator must manually re-encrypt subsequent records under a fresh symmetric key wrapped only to the remaining members. The old member's prior read-cap remains valid for ciphertext already fetched.
- §5.4 **Forward secrecy of the data itself** — a leaked record-level symmetric key reveals every record encrypted under that key. The mitigation suggested ("per-channel or per-time-window rekey + 'logical delete' via tombstone + republish under new key") was not specified.

ADR-2605231400 (consent capability) made this gap operational: when a patient revokes a consent capability granted to a grantee, the substrate cannot retroactively un-distribute ciphertext, but it MUST minimally prevent the grantee from decrypting NEW records that re-used the same symmetric key (because the prior records were wrapped to the grantee).

The constraint set:

- AT Protocol MST is append-only — physical delete is unavailable.
- IPFS pinning is similarly additive; the L2 anchor is monotonic.
- The substrate MUST remain "verifiable from outside any single operator" (ADR-2605172000 invariant).
- Recipients with cached read-caps can still decrypt past ciphertext; this is the cryptographic fact we cannot change.

# Decision

Introduce a typed **tombstone record** that operates as the substrate's logical-delete primitive and as the bind between rekey predecessor and successor. Add three XRPC procedures (`rekeyRecord` / `redactRecord` / `listTombstones`) that compose with `@etzhayyim/sdk.encryptedWrite` to express the three forms of "remove":

## Three tombstone kinds

| `tombstoneType` | Semantics | Cryptographic property |
|---|---|---|
| `rekey` | A successor envelope with a fresh symmetric key replaces the prior. Recipients (possibly reduced) get fresh key-wraps. | **Forward secrecy from now on** for new readers. Past readers retain access to prior ciphertext. |
| `redact` | Logical-delete with no successor. Future reads SHOULD treat the record as absent. Sender retains the sym_key in case of regulatory disclosure. | No new readers can be added. Past readers retain access. |
| `sealed` | Like `redact`, but the sender destroys its copy of the sym_key. No key-wrap can be issued again to anyone. | Sender + new readers permanently locked out; cached-key recipients still have access. |

## Scope (single vs windowed vs group)

| `scope` | Range | Use |
|---|---|---|
| `single-record` | Exactly the `supersededCid` envelope. | Data correction, patient-request individual redaction. |
| `channel-window` | All envelopes written by `actorDid` between `windowStart` and `windowEnd`. | Scheduled periodic rekey (e.g. monthly). |
| `group-rekey` | All envelopes whose key-wrap set included `removedRecipientDid`. | Member removal / consent revocation flush. |

The scope field is advisory — the actor still writes one tombstone per affected envelope (so each tombstone is a discrete signed claim). The scope value is the **declared intent** that a verifier reconstructing the timeline applies as the "why" annotation.

## Bind record (signature)

Every tombstone is Ed25519-signed by the actor that legitimately owns the underlying record:

- For the prior sender — for any reason except `regulator-order`.
- For a charter-authorized actor (Council Lv6+, etzhayyim-court) — for `regulator-order` only.

The signature covers the canonicalized payload (`supersededCid`, `successorCid`, `tombstoneType`, `reason`, `scope`, window fields, `actorDid`, `tombstoneAt`). Verifiers MUST reject unsigned or improperly-signed tombstones.

## Logical-present view algorithm

Consumers (e.g. `karute.getChartSummary`, FHIR Bundle export) compute the "logical present" timeline as:

```
present = records – { r | exists tombstone t : t.supersededCid == r.cid AND signed(t) }
                  + { r' | exists tombstone t : t.successorCid == r'.cid AND t.tombstoneType == "rekey" }
```

i.e. drop any record that has a tombstone superseding it, then add any successor that the same tombstone points forward to. Each consumer SHOULD evaluate this materializing pass on every read; caching is allowed but MUST refresh when a tombstone subscribeRepos event fires.

## Group-rekey-on-removal protocol

When `revokeConsent` fires for a grantee:

1. The substrate enumerates every envelope whose `keyWrap` set included `granteeDid` AND whose `granterDid` matches the revoker.
2. For each such envelope, the substrate (acting as the granter's automation, with the granter's signing key delegated via @etzhayyim/sdk) calls `rekeyRecord` with `reason='consent-revocation-flush'`, `removedRecipientDid=granteeDid`, `newRecipientDids=existingRecipients\{granteeDid}`.
3. Each rekey writes a new envelope, new key-wraps to remaining recipients, and a `tombstoneType='rekey'` tombstone with `scope='group-rekey'`.
4. The grantee's stale key-wrap is left in place (we cannot delete from MST) but no longer points to a current envelope.

Throughput note: at ~100 envelopes per minute the substrate sustains comfortable rekey rates. At >10⁴ pending flushes the rekey scheduler batches via a queue actor (deferred operational detail).

## Audit emission

Every tombstone with non-empty `auditWebhookDids` triggers an `com.etzhayyim.audit.event` (ADR-2605231700) per webhook target. This is the patient's observability mechanism for revocation-flush operations.

## Karute integration

The karute actor manifest gains three pipelines:

- `com.etzhayyim.apps.karute.rekeyRecord` — for prescriber-initiated correction or scheduled periodic rekey of long-lived chronic records (e.g. allergies list).
- `com.etzhayyim.apps.karute.redactRecord` — for mis-entered records (`reason='data-correction'`) and patient-initiated removal of non-mandatory fields.
- `com.etzhayyim.apps.karute.listTombstones` — for the chart-summary timeline materialization step.

The `getChartSummary` and `exportFhirBundle` pipelines are updated to apply the logical-present algorithm before returning.

# Consequences

## 正の効果

- **Forward secrecy from now on** for any rekey'd record. A future key compromise only exposes records since the most recent rekey.
- **Consent revocation has real-world teeth.** Grantee cannot decrypt new records after revocation, because the substrate rewrites those records under a fresh key wrapped only to the remaining set.
- **Logical delete on an append-only substrate.** Patients can request and receive redaction for non-mandatory fields; the audit timeline of the redaction is itself verifiable.
- **Charter-authorized override path exists** (`reason='regulator-order'`) without weakening the patient-sovereignty default for everything else.
- **Compositional.** Every primitive (envelope, key-wrap, tombstone) is independently signed and verifiable; the protocol stack doesn't require a special-case index.

## 負の効果 / コスト

- **Cached-key recipients retain access to historical ciphertext.** This is a fundamental cryptographic limit, not a bug — it is acknowledged in ADR-2605181100 §"No PCS for records." Mitigations: short read-cap caches, contractual obligations (clinician agreement / vendor agreement) to delete on revocation notification.
- **Group-rekey-on-removal is O(N) per affected envelope.** At very large group sizes (>10⁴) and high revocation churn the rekey scheduler becomes a real component. Deferred to operational ADR.
- **Storage cost grows.** Every rekey adds one envelope + N key-wraps + one tombstone. AT Protocol MST is cheap, but bookkeeping is not free. Expectation: <10× write amplification on normal usage.
- **Verifier complexity.** Every read pass must apply the logical-present algorithm. SDK enforces this at the seam (`encryptedRead` filters tombstoned CIDs by default; raw access requires explicit `includeTombstoned: true`).
- **Audit-event volume.** When a patient revokes a capability, the rekey-flush emits many events. The audit webhook subsystem (ADR-2605231700) MUST batch by event topic to avoid notification storms.
- **Sealed mode is irreversible.** Operators must be sure before invoking — a sealed envelope cannot be recovered even by court order.

## Rollout

1. **This commit** — Lexicons (tombstone + 3 XRPC) + ADR + karute actor manifest pipelines.
2. **Phase 2** — SDK seam (`@etzhayyim/sdk.encryptedRead` filters tombstoned by default; `@etzhayyim/sdk.rekeyRecord` helper that calls the procedure + maintains key-wrap bookkeeping).
3. **Phase 3** — Rekey-flush queue actor for high-volume consent revocations. Operational metric: time-to-flush after revocation.
4. **Phase 4** — `@etzhayyim/sdk.encryptedRead` strict-mode that requires every envelope to have either an absence of tombstone or a chain to a current successor. Currently lenient by default.

# Alternatives Considered

## A. Soft delete via metadata flag

Add `deleted: true` to envelope metadata. Rejected: AT Protocol records are immutable; you can't mutate the envelope. You'd need a delete record, which is exactly what a tombstone is.

## B. Aliased records (point CID A → CID B without a typed tombstone)

Use a generic "alias" record. Rejected: loses the typed reason / scope / signature affordances. A typed tombstone surfaces the operator's intent for audit and for the verifier's logical-present pass.

## C. Re-encryption (re-encrypt prior ciphertext with new key, write back in place)

AT Protocol records are immutable; in-place re-encryption is impossible. You can write a new record under a new key (which IS the rekey path), but you cannot delete the prior. Rejected as the standalone strategy; subsumed by the rekey + tombstone composition.

## D. Per-channel symmetric key (one key per recipient set, shared across records)

Reduces key-wrap fan-out cost. Rejected because (i) PCS is even weaker (one leaked key reveals every record in the channel), (ii) recipient-set changes propagate poorly (every channel-key change is a flush), (iii) cross-recipient correlation becomes possible from key reuse.

## E. Tombstone-as-metadata-on-envelope (write tombstone fields back into the original envelope record)

AT Protocol records are immutable — same blocker as A.

# References

- ADR-2605181100 [MST encrypted records + Signal key-wrap](./2605181100-mst-encrypted-records-signal-keywrap.md) §5.3 + §5.4 — the deferred items this ADR closes.
- ADR-2605231400 [karute consent capability + iryo billing bridge](./2605231400-karute-consent-capability-iryo-bridge.md) §"Revocation semantics" — the operational driver for group-rekey-on-removal.
- ADR-2605231700 [audit webhook subsystem](./2605231700-audit-webhook-subsystem.md) — emits per-tombstone events.
- AT Protocol Repository spec — https://atproto.com/specs/repository (append-only MST property)
- Signal Double Ratchet — https://signal.org/docs/specifications/doubleratchet/ (PCS contrast)
- MLS RFC 9420 §10 (epoch rekey semantics) — the model we approximate without adopting MLS itself.
