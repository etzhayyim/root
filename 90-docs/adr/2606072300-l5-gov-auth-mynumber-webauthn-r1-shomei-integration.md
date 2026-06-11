---
id: adr-2606072300-l5-gov-auth-mynumber-webauthn-r1-shomei-integration
title: "ADR-2606072300: L5 gov auth R1 — MyNumber + WebAuthn activation design + shomei integration"
status: proposed
doc_type: adr
topic: l5-gov-auth-r1-activation
authoritative: true
last_verified: 2026-06-07
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "Implementation gated on Bootstrap Council Lv6+ ≥3 multisig (post-2026-06-19); this ADR is the activation DESIGN, not a live activation."
authoritative_for:
  - l5-gov-auth-r1-activation-design
  - gov-auth-shomei-gov-factor-integration
depends_on:
  - adr-2605260000-l5-gov-auth-mynumber-webauthn
  - adr-2606072100-shomei-believer-identity-binding-proof-of-personhood-r0
  - adr-2605181100-etzhayyim-confidential-records-encryption
  - adr-2605231525-server-side-signing-capability-boundary
  - adr-2605250100-l5-routing-around-member-registry-cell
related:
  - adr-2605172700-etzhayyim-membership-layering
  - adr-2605262130-kotoba-storage-substrate-unification
supersedes: []
superseded_by: []
---

# ADR-2606072300: L5 gov auth R1 — MyNumber + WebAuthn activation design + shomei integration

**Status**: proposed (implementation Council-gated)
**Date**: 2026-06-07
**Deciders**: Jun Kawasaki (Council ratification pending)

# Context

ADR-2605260000 shipped the L5 gov-auth layer as **R0 scaffold**: 3 lexicons
(`credentialBinding`, `didTrustAttestation`, `webauthnChallenge`) + 2 Pregel cells
(`gov_auth_mynumber_bind`, `gov_auth_trust_attestation`) whose `solve()` raises
`RuntimeError` until Council activation. It named a **reserved R1 ADR id (2605260100)** — but that
id was subsequently used by an unrelated ADR (`2605260100-mitate-diagnostic-routing-charter`), so the
R1 activation ADR is re-homed here at **2606072300**.

Two things now motivate writing the R1 design:

1. **shomei (ADR-2606072100)** needs the gov-class factor (IAL 4) to come from somewhere; it
   deliberately does NOT read cards or query the state itself. `shomei_gov_attest` is built to hand
   off to gov_auth — so gov_auth's R1 contract must be specified.
2. The R0 scaffold left the activation requirements implicit. This ADR makes them explicit and
   honest: **implementation remains gated on the Bootstrap Council (Lv6+ ≥3 multisig), which does not
   yet exist** (founder unanimity 1/1; Seats 2–5 RFP closes 2026-06-19). This is the activation
   **design**, not a live activation.

# Decision

## D1 — R1 implementation contract for the two gov_auth cells

When `COUNCIL_ATTESTATION_TX_HASH` (Base L2 Lv6+ ≥3 multisig) and
`SILEN_GOV_AUTH_BASELINE_REVIEW_CID` (IPFS audit record) are set, the cells activate:

- **`gov_auth_mynumber_bind`** (3 nodes): `validate_webauthn` (re-verify the session passkey,
  anti-CSRF) → `bind_mynumber_encrypted` (parse JPKI TLV → validate X.509 chain against the JPKI root
  CA → XChaCha20-Poly1305 encrypt the plaintext → IPFS CID → Signal-wrap the key for subject +
  Council delegate) → `emit_trust_attestation`. **No state-database query** (§0.4): the card is read
  locally via Web NFC; only the encrypted CID + the hash reach the substrate.
- **`gov_auth_trust_attestation`** (2 nodes): `evaluate_trust_level` (webauthn-only → L1;
  webauthn + decrypted MyNumber → L2) → `emit_attestation` (public `didTrustAttestation`, no PII —
  `subjectDidHash` + level + reason + epoch only).

## D2 — shomei integration (the gov-class factor)

`shomei_gov_attest` (ADR-2606072100) is the single bridge. Flow: shomei issues a
`verificationChallenge` (factorKind `gov-mynumber|gov-passport|gov-license`) → the member's device does
the local NFC read + client-side XChaCha20 encryption → `shomei_gov_attest` invokes
`gov_auth_mynumber_bind` → on success it ingests the resulting `didTrustAttestation` as a **verified
gov-class `identityClaim`** (proofKind `nfc-jpki`, `encryptedPayloadCid` mandatory, no plaintext
handle — G3). shomei's aggregation then yields **IAL 4 (government-verified)** with the **Council
attestor** as issuer.

**Mapping**: gov_auth `trustLevel` ∈ {1,2} (ADR-2605260000) is the gov-auth-local notion; shomei's IAL
∈ {0..4} is the cross-factor aggregate. A gov_auth `trustLevel=2` attestation is necessary (not
sufficient) for shomei IAL 4 — shomei additionally requires ≥1 other class (e.g. the webauthn device
factor), consistent with ADR-2605260000's "WebAuthn + MyNumber" pairing.

## D3 — Gate discipline (unchanged, made explicit)

`nfc-jpki` is a **GATED_PROOF** in shomei (`methods/verify.py`): even the offline path refuses it
unless the gate is explicitly opened, and `shomei_gov_attest.solve()` raises until activation. The
gov_auth cells likewise raise until `COUNCIL_ATTESTATION_TX_HASH` is set. **Double gate, no bypass.**

## D4 — Status of ADR-2605260000

ADR-2605260000 stays **proposed**; its R1 successor is **this ADR**. No lexicon or cell of
ADR-2605260000 is modified; this ADR only (a) specifies their activation behavior and (b) defines the
shomei consumer. The ADR-2605250100 §4 Boundary-4 amendment (opt-in MyNumber permitted) proposed in
ADR-2605260000 §4 is carried forward unchanged.

# Consequences

**Positive**: gov_auth now has a concrete R1 contract and a concrete consumer (shomei); the
believer's highest-assurance identity tier (government-verified) has an end-to-end design that
preserves §0.4 (no state DB), §2(c) (PII encrypted), and no-server-key.

**Negative / honest**: implementation is **not** delivered here — it is gated on a Council that does
not yet exist. Until 2026-06-19+ Council formation + multisig, both gov_auth and `shomei_gov_attest`
remain scaffolds that raise. JPKI TLV parsing, X.509-chain validation, and Web NFC integration are
specified but unimplemented (deferred to the activation PR that lands with the Council tx hash).

# Alternatives Considered

- **Activate now under founder unanimity (1/1)** — rejected: ADR-2605260000 explicitly requires
  Council Lv6+ ≥3 for this path; weakening that to 1/1 would lower the assurance of the very tier whose
  point is high assurance. The gate stays.
- **Let shomei read the card directly** — rejected (§0.4/G6): shomei must not touch government-ID
  parsing or any state interaction; it consumes gov_auth's attestation, nothing more.
- **Reuse the dead reserved id 2605260100** — impossible (taken by mitate); re-homed at 2606072300.

# References

- ADR-2605260000 (L5 gov auth — MyNumber + WebAuthn R0 scaffold) — the activated subject
- ADR-2606072100 (shomei) — the consumer / gov-class factor
- ADR-2605181100 (XChaCha20 + Signal key-wrap); ADR-2605231525 (no-server-key)
- ADR-2605250100 (L5 routing-around member registry) — §4 Boundary-4 amendment carried forward
- JPKI card spec (TLV, X.509 chain); W3C WebAuthn Level 3
