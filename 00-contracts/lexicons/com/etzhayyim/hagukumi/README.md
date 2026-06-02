# com.etzhayyim.hagukumi.* — Lexicons

Per ADR-2605261030. R0 stubs; full schemas R1+.

**PRIVACY INVARIANT** (CRITICAL): `careSessionAttestation` enforces `additionalProperties: false` + mandatory `encryptedPayloadCid` (XChaCha20 envelope per ADR-2605181100). Any plaintext content field is structurally rejected.

| Lexicon | Purpose |
|---|---|
| `caregiverAttestation` | Caregiver onboarding (G4: training + background + Council Lv6+ ≥3 vetting) |
| `careSessionAttestation` | Per-session record (mandatory encrypted payload; aggregate-only public) |
| `consentRecord` | Care-recipient + family-guardian consent (revocable, on-chain) |
| `silenCareReview` | Council attestation scope (privacy + Wellbecoming + multi-gen ratio) |

## Related ADRs

- ADR-2605261030 — hagukumi master ADR
- ADR-2605261000 — Liberation Ladder L4 gate
- ADR-2605181100 — Encrypted records envelope (privacy invariant)
- ADR-2605181200 — Rotating pseudonym DID (recipient identity)
- ADR-2605260100 — mitate cross-actor sibling
