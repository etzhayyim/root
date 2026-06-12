#!/usr/bin/env python3
"""post_quantum-compat — pqh-v1 suite + migration-state SSoT (ADR-2606111300).

The machine-readable registry of WHERE the substrate stands against the
quantum/HNDL threat analysed in 90-docs/security/2606111200: which crypto
layer runs which primitive, whether Shor or only Grover applies, what suite
it migrated to, and what remains operator-/chain-/upstream-gated. The
companion paper's §7 table, as data — so coverage can be asserted by tests
instead of believed.

Pure stdlib — runnable inside the kotoba pywasm actor (componentize-py).
Non-eschatological framing per Charter §1.15: dated, measurable risk
management (Mosca inequality), not prophecy.
"""
from __future__ import annotations

# ── suite registry (FIPS 203/204 + RFC 9106 constants) ──────────────────────

SUITES = {
    ":suite/pqh-v1": {
        ":suite/id": "pqh-v1",
        ":suite/adr": "ADR-2606111300",
        ":suite/kem": {
            ":kem/classical": "X25519",
            ":kem/pq": "ML-KEM-768",
            ":kem/pq-fips": "FIPS 203",
            ":kem/combiner": "HKDF-SHA256 transcript-bound (X-Wing pattern)",
            ":kem/pq-public-bytes": 1184,
            ":kem/pq-ciphertext-bytes": 1088,
            ":kem/shared-secret-bytes": 32,
            ":kem/pq-multicodec": 0x120C,  # mlkem-768-pub (draft)
        },
        ":suite/sig": {
            ":sig/classical": "Ed25519",
            ":sig/pq": "ML-DSA-65",
            ":sig/pq-fips": "FIPS 204",
            ":sig/composition": "dual signature, verifier requires both (AND)",
            ":sig/pq-public-bytes": 1952,
            ":sig/pq-signature-bytes": 3309,
            ":sig/pq-multicodec": 0x1211,  # mldsa-65-pub (draft)
        },
        ":suite/kdf": {
            ":kdf/id": "argon2id-v1",
            ":kdf/rfc": "RFC 9106",
            ":kdf/default-m-kib": 19456,
            ":kdf/default-t": 2,
            ":kdf/default-p": 1,
        },
    },
}

# ── layer migration registry (the paper's §7 table as data) ─────────────────
# :layer/status enum:
#   :migrated          pqh-v1 landed in code (PR refs below)
#   :adequate          Grover-bounded only — no migration needed by design
#   :operator-pending  code landed; production key/flag flip is an operator step
#   :chain-blocked     cannot migrate unilaterally (Base L2 / ERC-4337 constraint)
#   :upstream-pending  waiting on a dependency's own PQ release
#   :deferred          surface not live yet; migrate when it ships

LAYERS = [
    {":layer/id": ":layer/record-at-rest", ":layer/primitive": "XChaCha20-Poly1305-256",
     ":layer/quantum-attack": ":grover", ":layer/status": ":adequate",
     ":layer/adr": "ADR-2605181100"},
    {":layer/id": ":layer/vault-at-rest", ":layer/primitive": "AES-256-GCM",
     ":layer/quantum-attack": ":grover", ":layer/status": ":adequate",
     ":layer/adr": "ADR-2605181100"},
    {":layer/id": ":layer/hashes", ":layer/primitive": "SHA-256/Keccak-256/BLAKE2b",
     ":layer/quantum-attack": ":grover", ":layer/status": ":adequate",
     ":layer/adr": "ADR-2606111300"},
    {":layer/id": ":layer/key-wrap", ":layer/primitive": "X25519",
     ":layer/quantum-attack": ":shor", ":layer/status": ":migrated",
     ":layer/suite": "pqh-v1", ":layer/adr": "ADR-2606111300", ":layer/pr": [1616, 1621]},
    {":layer/id": ":layer/did-signal-binding", ":layer/primitive": "Ed25519",
     ":layer/quantum-attack": ":shor", ":layer/status": ":migrated",
     ":layer/suite": "pqh-v1", ":layer/adr": "ADR-2606111300", ":layer/pr": [1616]},
    {":layer/id": ":layer/did-doc-attestation", ":layer/primitive": "Ed25519",
     ":layer/quantum-attack": ":shor", ":layer/status": ":migrated",
     ":layer/suite": "pqh-v1", ":layer/adr": "ADR-2606111300", ":layer/pr": [1630],
     ":layer/note": "requirePq/expectedPqDidKey enforcement flip = operator step"},
    {":layer/id": ":layer/password-kdf", ":layer/primitive": "PBKDF2-SHA256",
     ":layer/quantum-attack": ":grover", ":layer/status": ":migrated",
     ":layer/suite": "argon2id-v1", ":layer/adr": "ADR-2606111300", ":layer/pr": [1625],
     ":layer/note": "T3 implementation-layer hardening, not a quantum fix"},
    {":layer/id": ":layer/production-pq-keys", ":layer/primitive": "ML-DSA-65 did:key",
     ":layer/quantum-attack": ":shor", ":layer/status": ":operator-pending",
     ":layer/suite": "pqh-v1", ":layer/adr": "ADR-2606111300",
     ":layer/note": "sign-diddoc.mjs --pq exists; key generation/publication is operator-held (no-server-key)"},
    {":layer/id": ":layer/governance-signature", ":layer/primitive": "secp256k1-ECDSA",
     ":layer/quantum-attack": ":shor", ":layer/status": ":chain-blocked",
     ":layer/adr": "ADR-2606111300",
     ":layer/note": "Base L2 / ERC-4337 constraint; mitigation = key rotation + spend-before-z"},
    {":layer/id": ":layer/libsignal-path", ":layer/primitive": "X25519-X3DH",
     ":layer/quantum-attack": ":shor", ":layer/status": ":upstream-pending",
     ":layer/note": "upstream PQXDH adoption via optional-dependency bump"},
    {":layer/id": ":layer/passkey-signature", ":layer/primitive": "P-256-ES256",
     ":layer/quantum-attack": ":shor", ":layer/status": ":deferred",
     ":layer/note": "surface not live (future R2 federated training); WebAuthn PQ tracked"},
]

MIGRATION_DONE = {":migrated", ":adequate"}
GATED = {":operator-pending", ":chain-blocked", ":upstream-pending", ":deferred"}


# ── math helpers (testable, from the survivability paper) ────────────────────

def grover_effective_bits(key_bits: int) -> int:
    """BBBV-proved quadratic bound: brute force of an n-bit key costs 2^(n/2)."""
    return key_bits // 2


def mosca(x_shelf_life_years: float, y_migration_years: float,
          z_crqc_years: float) -> dict:
    """Mosca inequality: act now iff x + y > z. Returns the slack either way."""
    slack = z_crqc_years - (x_shelf_life_years + y_migration_years)
    return {":mosca/act-now": slack < 0, ":mosca/slack-years": slack}


def shor_applies(layer: dict) -> bool:
    return layer.get(":layer/quantum-attack") == ":shor"


# ── coverage readout (DERIVED — computed on read, never stored) ──────────────

def coverage_report() -> dict:
    shor = [l for l in LAYERS if shor_applies(l)]
    migrated = [l for l in shor if l[":layer/status"] == ":migrated"]
    gated = [l for l in shor if l[":layer/status"] in GATED]
    unknown = [l for l in LAYERS
               if l[":layer/status"] not in MIGRATION_DONE | GATED]
    return {
        ":coverage/layers-total": len(LAYERS),
        ":coverage/shor-vulnerable": len(shor),
        ":coverage/migrated": len(migrated),
        ":coverage/gated": len(gated),
        ":coverage/unknown": len(unknown),
        ":coverage/migrated-fraction": round(len(migrated) / len(shor), 4),
        ":coverage/gated-ids": sorted(l[":layer/id"] for l in gated),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(coverage_report(), indent=2, ensure_ascii=False))
