"""factors.py — 証明 (shomei) factor taxonomy + assurance ladder (SSoT). ADR-2606072100.

The single source the lexicons + invariant tests parse. Every external-identity factor
maps to exactly one independence CLASS; the Identity Assurance Level (IAL) is a pure
function of the SET of verified factor classes — never of the person (G8).

Stdlib only.
"""
from __future__ import annotations

# factorKind → factorClass (independence class). G8: assurance counts DISTINCT classes,
# so two key-class wallets (EVM + BTC) raise count but not class-diversity.
FACTOR_CLASS: dict[str, str] = {
    "webauthn": "device",
    "wallet-evm": "key",
    "wallet-btc": "key",
    "sns-github": "social",
    "sns-x": "social",
    "sns-google": "social",
    "sns-apple": "social",
    "gov-mynumber": "government",
    "gov-passport": "government",
    "gov-license": "government",
    "etz-base-membership": "covenant",
    "etz-adherent-sbt": "covenant",
    "etz-at-oath": "covenant",
}

CLASSES = ("device", "key", "social", "government", "covenant")

# factorKind → allowed proofKinds (G4 cryptographic-proof-mandatory: a claim whose
# proofKind is not in this set for its factorKind is structurally invalid).
ALLOWED_PROOFS: dict[str, frozenset[str]] = {
    "webauthn": frozenset({"webauthn-assertion"}),
    "wallet-evm": frozenset({"eip191", "eip1271"}),
    "wallet-btc": frozenset({"bip322"}),
    "sns-github": frozenset({"oauth-sub", "signed-gist", "dns-txt"}),
    "sns-x": frozenset({"oauth-sub"}),
    "sns-google": frozenset({"oauth-sub"}),
    "sns-apple": frozenset({"oauth-sub"}),
    "gov-mynumber": frozenset({"nfc-jpki"}),
    "gov-passport": frozenset({"nfc-jpki"}),
    "gov-license": frozenset({"nfc-jpki"}),
    "etz-base-membership": frozenset({"base-l2-event"}),
    "etz-adherent-sbt": frozenset({"erc5192-sbt"}),
    "etz-at-oath": frozenset({"at-record-sig"}),
}

FACTOR_KINDS = frozenset(FACTOR_CLASS)
PROOF_KINDS = frozenset(p for ps in ALLOWED_PROOFS.values() for p in ps)

# G3: government factors carry NO plaintext identifier; encryptedPayloadCid is mandatory.
GOV_FACTORS = frozenset(k for k, c in FACTOR_CLASS.items() if c == "government")
COVENANT_FACTORS = frozenset(k for k, c in FACTOR_CLASS.items() if c == "covenant")
# Only inherently-public, pseudonymous factors may carry a plaintext externalHandle.
PUBLIC_HANDLE_FACTORS = frozenset(
    k for k in FACTOR_CLASS if k.startswith("wallet-") or k.startswith("sns-")
)
# G11: gov L2 proof is Council-gated (ADR-2605260000); the R0 cell .solve() raises.
GATED_PROOFS = frozenset({"nfc-jpki"})

REVOCATION_REASONS = frozenset(
    {"key-rotated", "key-lost", "account-closed", "compromised", "superseded", "voluntary"}
)


def factor_class(kind: str) -> str:
    if kind not in FACTOR_CLASS:
        raise ValueError(f"unknown factorKind: {kind!r}")
    return FACTOR_CLASS[kind]


def assurance_level(classes: set[str], count: int) -> int:
    """Identity Assurance Level from the set of verified factor classes + factor count.

    0 did-only · 1 self-attested (≥1 factor) · 2 multi-factor (≥2 factors, ≥2 classes) ·
    3 covenant-bound (IAL2 + a covenant etzhayyim factor) · 4 government-verified
    (a gov factor paired with ≥1 other class; Council-attested, ADR-2605260000).
    """
    n = len(classes)
    if count == 0:
        return 0
    if "government" in classes and n >= 2:
        return 4
    if "covenant" in classes and n >= 2 and count >= 2:
        return 3
    if n >= 2 and count >= 2:
        return 2
    return 1


def proof_of_personhood(level: int, n_classes: int) -> bool:
    """Sybil-RESISTANCE (not sybil-proof): ≥2 independent classes. Never a person ranking."""
    return level >= 2 and n_classes >= 2
