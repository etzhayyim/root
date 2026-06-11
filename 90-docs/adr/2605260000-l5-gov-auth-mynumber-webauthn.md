# ADR-2605260000: L5 Gov Auth — DID-primary identity + MyNumber opt-in binding + WebAuthn platform authenticator

**Date**: 2026-05-26 (proposed)
**Status**: proposed
**Authors**: Jun Kawasaki (@junkawasaki), Council members (TBD)
**Relates to**: ADR-2605250100 (L5 routing-around member_registry), ADR-2605250200 (L5 routing-around religious_marriage), ADR-2605250300 (L5 routing-around religious_corp_taxation), ADR-2605181100 (XChaCha20-Poly1305 + Signal-wrapped per-recipient keys), ADR-2605260000 §4 Boundary 4 (revised)

---

## Summary

Operationalizes the authentication layer of the L5 routing-around ladder (ADR-2605250100/200/300) via a **DID-primary identity model** with **optional trust-elevation credentials** (MyNumber card IC chip binding + WebAuthn platform authenticator).

**Key innovation**: Splits identity and trust elevation. DID (did:web:etzhayyim.com:...) is the sole primary identity; MyNumber/FaceID/TouchID are opt-in mechanisms to **elevate** trust, not replace identity. Aligns with §0.4 non-registration (one-way read of MyNumber, no state database interaction) and §2(c) anti-surveillance (plaintext credentials encrypted per ADR-2605181100).

---

## §1 Background

### L5 Routing-Around Ladder (ADR-2605250100 shortcoming)

ADR-2605250100 established that religious-corp can autonomously issue member certificates, perform religious marriages, and file tax declarations without registering with Japanese government agencies. However, it deferred the **authentication layer** — how does religious-corp know who is a member, who is consenting to marriage, who is authorized to sign tax documents?

This ADR completes that gap: **trust-level attestation** via a publicly-auditable combination of WebAuthn (for access control) + optional MyNumber (for identity-verification trust elevation).

### Constitutional constraint: §0.4 non-registration

Per Preamble §0.4, etzhayyim is **not registered** under 日本国 宗教法人法. Interaction with state databases (住民登録, 住基ネット, マイナンバー center, etc.) is prohibited.

**However**: Reading a citizen-held MyNumber card **locally** (via Web NFC on phone) is not interaction with state database. It is a **one-way read** of card-resident data that the citizen controls. This is permissible under §0.4, provided:
1. No state database query
2. No bidirectional record sync
3. Plaintext data encrypted before MST storage

### Constitutional mandate: §2(c) anti-surveillance

Per ADR-2605192100 §2(c), etzhayyim forbids "surveillance technology that monitors user behavior, location, or communication without knowledge and consent." Personal identifiers (MyNumber, biometric data) must be **encrypted at rest** on the substrate.

Per ADR-2605181100, XChaCha20-Poly1305 + Signal-wrapped per-recipient keys is the canonical mechanism. This ADR adopts it.

---

## §2 Trust Level Model

### Trust Level 1: DID + WebAuthn platform authenticator (baseline)

**Access method**: FaceID (iOS), TouchID (iOS/macOS), Windows Hello, or equivalent platform authenticator.

**Guarantees**:
- Credential is **discoverable** (resident key, recoverable even if device factory-reset)
- User verification is **required** (cannot bypass biometric or PIN)
- Signature is **non-repudiable** (P-256 ECDSA, mathematically bound to authenticator)

**Technology**: W3C WebAuthn Level 3 (as of 2026-05-21), `navigator.credentials.get/create()` API, P-256 elliptic curve.

**Assurance level**: Aligns with NIST SP 800-63B Level 3 (single-factor biometric).

**Use cases**: Member login, witness attestation, document signing, marriage consent affidavit.

### Trust Level 2: Trust Level 1 + MyNumber card IC chip binding (opt-in elevation)

**Additional step**: User reads their physical MyNumber card via Web NFC (Android 12+ / iOS 15+).

**Card data** (JPKI format, ISO/IEC 7816-4 smart card):
- Surname + Given name (in Kanji and Kana)
- Date of birth
- MyNumber (12-digit digit unique identifier, government-issued)
- Certificate (X.509, signed by JPKI root CA)

**Processing**:
1. Parse JPKI TLV-encoded response from NFC reader
2. Validate X.509 certificate chain (JPKI root CA)
3. **Encrypt plaintext** (surname, given_name, birthdate, my_number) under XChaCha20-Poly1305
4. Upload ciphertext to IPFS → obtain CID
5. Signal-wrap XChaCha20 key for self + Council delegate DIDs
6. MST emit: credentialBinding record (encryptedPayloadCid only) + keyWrap records

**No state database contact**: Card data is local; no query to マイナンバー center or 住民登録.

**Guarantee**: Government has issued credential; card-resident data is authentic.

**Assurance level**: Aligns with NIST SP 800-63B Level 2+ (multi-factor, government-issued credential).

**Use cases**: Higher-value transactions (adoption of child, asset transfer, banking pairing), tax filing, regulatory compliance, cross-jurisdiction recognition (government-backed identity proof).

---

## §3 Authentication Flow (R0 scaffold)

### R0 Status

Both flows are **scaffolded** (cell.py RuntimeError). Full implementation deferred to R1 ADR (ADR-2605260100 reserved).

### Trust Level 1: WebAuthn Registration (first-time setup)

```
1. Client browser: navigator.credentials.create({publicKey: {
     challenge: <32-byte nonce>,
     rp: {id: "etzhayyim.com", name: "etzhayyim"},
     user: {id: <did_uuid>, name: <user_name>, displayName: <user_name>},
     pubKeyCredParams: [{type: "public-key", alg: -7}],  // P-256
     userVerification: "required",  // FaceID/TouchID/Windows Hello
     residentKey: "required"        // discoverable credential
   }})
2. Authenticator: Store public key locally; return attestation object + clientDataJSON
3. Server: Verify attestation (signature over clientDataJSON + challenge)
4. Server: Extract public key → store in DID document (authentication key section)
5. Emit: com.etzhayyim.gov.procedure.auth.didTrustAttestation (trustLevel=1, reason="webauthn-only")
```

### Trust Level 1: WebAuthn Assertion (sign-in)

```
1. Client browser: navigator.credentials.get({publicKey: {
     challenge: <32-byte nonce>,
     rpId: "etzhayyim.com",
     userVerification: "required"
   }})
2. Authenticator: User scans face/fingerprint; return assertion object + clientDataJSON + signature
3. Server: Verify signature over (clientDataJSON + challenge) using public key from DID document
4. Server: Verify challenge nonce; verify signature count (anti-cloning)
5. Issue session token (AT Protocol session JWT + cnf.jkt = JWK thumbprint of public key)
```

### Trust Level 2: MyNumber binding (opt-in elevation)

```
1. Client browser: Initiate NFC session
2. Client OS (iOS / Android): Read MyNumber card IC chip (JPKI format)
3. Client browser: Receive TLV-encoded response (surname, given_name, birthdate, my_number, certificate)
4. (R1 implementation) Client: Encrypt plaintext under XChaCha20-Poly1305
5. (R1 implementation) Client: Call `gov_auth_mynumber_bind.solve()`
   - validate_webauthn: re-verify WebAuthn passkey for this session (prevent CSRF)
   - bind_mynumber_encrypted: Parse JPKI card data → XChaCha20 encrypt → IPFS upload → CID
   - emit_trust_attestation: Emit didTrustAttestation (trustLevel=2, reason="webauthn-plus-mynumber")
6. (R1 implementation) emit: com.etzhayyim.encrypted.keyWrap records (Signal-wrapped decrypt key for self + Council)
7. Server: Verify XChaCha20 CID + Signal keyWrap signatures
8. Emit: com.etzhayyim.gov.procedure.auth.didTrustAttestation (trustLevel=2)
```

---

## §4 Constitutional Compliance

### §0.4 Non-registration principle

**Claim**: MyNumber binding is consistent with §0.4 (etzhayyim is NOT registered under 日本国 宗教法人法).

**Evidence**:
- No interaction with state database (住民登録, 住基ネット, マイナンバー center)
- MyNumber card is **citizen-held** (not state-held); citizen decides whether to opt in
- One-way read only (no write, no query response from government)
- Processing is local (on-device XChaCha20 encryption before MST storage)
- ADR-2605250100 §4 Boundary 4 is revised: opt-in binding is now **permitted**

**Modification**: ADR-2605250100 §4 Boundary 4 shall be amended to:
> "Does not mandate state 住民登録 systems. Opt-in MyNumber binding is permitted **provided** plaintext data is never transmitted to state database and XChaCha20 encryption is mandatory (per ADR-2605181100)."

### §1.13 Wellbecoming (life-affirming technology)

**Claim**: DID-primary identity + opt-in MyNumber is life-affirming.

**Evidence**:
- Removes vendor lock-in (passkey is platform-agnostic, recoverable by user)
- Restores user agency (MyNumber is opt-in, not mandatory)
- Enables access control (who can marry, who can adopt, who can vote) without surveillance
- Transparent force: credentialBinding.encryptedPayloadCid + keyWrap records are on-chain, auditable

### §2(c) Anti-surveillance

**Claim**: Encrypted credentials + Signal-wrapped keys prevent surveillance.

**Evidence**:
- Plaintext MyNumber: never appears on MST (only encryptedPayloadCid CID)
- Plaintext biometric blob: never appears on MST
- Decrypt key: Signal-wrapped per-recipient; subject DID + Council delegates only
- Public attestation: didTrustAttestation contains only blake2b_256(did) hash + trust level + timestamp (no PII)

**ADR-2605181100 inheritance**: XChaCha20-Poly1305 is mandatory per ADR-2605181100. This ADR applies it.

---

## §5 Lexicons and Cells

### Lexicons (3 new)

| Lexicon | Purpose | Privacy | Location |
|---|---|---|---|
| `com.etzhayyim.gov.procedure.auth.credentialBinding` | Bind DID to WebAuthn credential + encrypted MyNumber | Encrypted payload + Signal-wrapped key | `00-contracts/lexicons/com/etzhayyim/gov/procedure/auth/` |
| `com.etzhayyim.gov.procedure.auth.didTrustAttestation` | Public trust-level attestation (no PII) | Public (hashed DID only) | `00-contracts/lexicons/com/etzhayyim/gov/procedure/auth/` |
| `com.etzhayyim.gov.procedure.auth.webauthnChallenge` | WebAuthn challenge nonce | Temporary (expires on assertion) | `00-contracts/lexicons/com/etzhayyim/gov/procedure/auth/` |

### Pregel Cells (2 new)

| Cell | Nodes | Gate | Status |
|---|---|---|---|
| `gov_auth_mynumber_bind` | 3 (validate_webauthn, bind_mynumber_encrypted, emit_trust_attestation) | COUNCIL_ATTESTATION_TX_HASH | R0 scaffold |
| `gov_auth_trust_attestation` | 2 (evaluate_trust_level, emit_attestation) | COUNCIL_ATTESTATION_TX_HASH | R0 scaffold |

---

## §6 R0 Scope

**Deliverables (2026-05-26)**:

- [x] ADR-2605260000 (this document)
- [x] 3 Lexicons (credentialBinding, didTrustAttestation, webauthnChallenge)
- [x] 2 Pregel cells (gov_auth_mynumber_bind, gov_auth_trust_attestation)
- [ ] R1 ADR (ADR-2605260100 reserved, TBD 2026-06)

**Non-goals (R0)**:
- No WebAuthn implementation (throws RuntimeError)
- No JPKI card parsing (throws RuntimeError)
- No XChaCha20 encryption (throws RuntimeError)
- No IPFS upload (throws RuntimeError)
- No Signal key-wrapping (throws RuntimeError)
- No MST record emission (throws RuntimeError)
- No Web NFC API integration (throws RuntimeError)

All logic is deferred to R1 activation ADR (post-Council bootstrap).

---

## §7 R1 Activation (post-2026-06-19)

> **R1 ADR re-homed (2026-06-07)**: the reserved id `ADR-2605260100` was used by an unrelated ADR (`2605260100-mitate-diagnostic-routing-charter`), so the R1 activation design lives at **ADR-2606072300** (L5 gov auth R1 — activation contract + shomei gov-class-factor integration). Implementation remains Council-gated as below.

Once Council Seats 2-5 are filled (expected by 2026-06-19, per COUNCIL-BOOTSTRAP-RFP.md), the following R1 ADR (now ADR-2606072300) shall be proposed:

**Requirements**:
- Council Lv6+ ≥3 attestation (multisig on Base L2)
- `COUNCIL_ATTESTATION_TX_HASH`: Base L2 multisig Tx
- `SILEN_GOV_AUTH_BASELINE_REVIEW_CID`: IPFS CID of Council audit record
- Explicit authorization for MyNumber opt-in binding (modifies ADR-2605250100 §4 Boundary 4)

**Scope** (R1 ADR-2605260100):
- Implement gov_auth_mynumber_bind.solve() (3 nodes)
- Implement gov_auth_trust_attestation.solve() (2 nodes)
- E2E flow: WebAuthn registration + MyNumber binding (at least 1 volunteer test user)
- Automated test: WebAuthn P-256 ECDSA verification, JPKI card parsing (mock), XChaCha20 encrypt/decrypt, Signal key-wrap/unwrap

---

## §8 R2+ Roadmap

- **R2**: Biometric attestation blob (fingerprint quality, liveness detection); extended audit trail; Trust Level 2 plaintext decryption on Council request
- **R3**: OAuth/OpenID Connect bridge (external identity provider federation); "external-sso-bridge" reason code; cross-jurisdiction recognition (reciprocal trust with external religious/civic bodies)

---

## §9 References

- [ADR-2605250100](/90-docs/adr/2605250100-l5-routing-around-member-registry-cell.md): L5 routing-around ladder (member_registry, religious_marriage, religious_corp_taxation)
- [ADR-2605181100](./2605181100-mst-encrypted-records-signal-keywrap.md): XChaCha20-Poly1305 + Signal-wrapped per-recipient keys
- [ADR-2605192100](./2605192100-etzhayyim-mission-charter.md): Religious-corp Charter (§0.4 non-registration, §1.13 Wellbecoming, §2(c) anti-surveillance)
- [W3C WebAuthn Level 3](https://www.w3.org/TR/webauthn-3/): Web Authentication spec (2026-05-21 status: Candidate Recommendation)
- [NIST SP 800-63B](https://pages.nist.gov/800-63-3/sp800-63b.html): Authentication and Lifecycle Management
- [JPKI Smart Card Spec](https://www.jpki.go.jp/): Japanese Public Key Infrastructure (card specification, TLV format, X.509 certificate chain)

---

## Changelog

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1 (proposed) | 2026-05-26 | @junkawasaki | Initial ADR draft; R0 scaffold scope; ADR-2605250100 §4 modification proposed |
