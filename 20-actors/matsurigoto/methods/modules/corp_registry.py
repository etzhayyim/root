#!/usr/bin/env python3
"""matsurigoto 政 — `corp-registry` module (R0 reference implementation).

ADR-2606062300. Third executable vertical slice: company-registry engine behind
`corp.incorporation.register` / `corp.change.register` / `corp.certificate` — i.e. 法人登記.

WHAT IT IS: pure-function VALIDATION + registry-number assignment + ISO 17442 **LEI** issuance
with a real **ISO 7064 MOD 97-10** check-digit computation (the same check class as IBAN; the
conformance anchor of this module, like the JP 速算表 for tax-assess), then an APPEND-ONLY
record + an UNSIGNED incorporation certificate.

Spec basis (G2): ISO 17442 (LEI) + GLEIF LEI-CDF + EU BRIS + W3C VC 2.0.

Charter invariants:
  G1 no-operator-master-key : SERVER_HELD_AUTHORITY False; certificate UNSIGNED (the governing
                              organ signs with ITS own key, never this module).
  G2 spec-derived-only      : ISO 17442 LEI structure + ISO 7064 MOD 97-10 checksum.
  G5 append-only (非終末論)  : a change is an appended amendment record; nothing is overwritten.

stdlib only, no I/O, no network. Importable as a kotoba-wasm module contract.
"""
from __future__ import annotations

SERVER_HELD_AUTHORITY = False  # G1


# ── ISO 17442 LEI + ISO 7064 MOD 97-10 (the conformance anchor) ──
def _to_digits(s: str) -> str:
    """Convert an alphanumeric string to its ISO 7064 numeric form (0-9 stay; A=10 … Z=35)."""
    out = []
    for ch in s:
        if ch.isdigit():
            out.append(ch)
        elif "A" <= ch <= "Z":
            out.append(str(ord(ch) - 55))  # 'A'(65) → 10
        else:
            raise ValueError(f"LEI char must be [0-9A-Z], got {ch!r}")
    return "".join(out)


def compute_lei_check_digits(base18: str) -> str:
    """ISO 7064 MOD 97-10 check digits for an 18-char LEI base (LOU 4 + reserved 2 + entity 12).

    digits = numeric(base18 + "00"); check = 98 − (digits mod 97); zero-padded to 2.
    By construction numeric(base18 + check) mod 97 == 1 (proven algebraically), so validate_lei
    accepts the assembled LEI — and flipping any character breaks it (prob 96/97).
    """
    if len(base18) != 18:
        raise ValueError(f"LEI base must be 18 chars, got {len(base18)}")
    mod = int(_to_digits(base18 + "00")) % 97
    return f"{98 - mod:02d}"


def validate_lei(lei: str) -> bool:
    """A 20-char LEI is valid iff numeric(lei) mod 97 == 1 (ISO 7064 MOD 97-10)."""
    if not isinstance(lei, str) or len(lei) != 20:
        return False
    try:
        return int(_to_digits(lei)) % 97 == 1
    except ValueError:
        return False


def assign_lei(lou_prefix: str, entity_id12: str) -> str:
    """Build a valid LEI: 4-char LOU prefix + reserved '00' + 12-char entity id + 2 check digits."""
    if len(lou_prefix) != 4:
        raise ValueError("LOU prefix must be 4 chars")
    if len(entity_id12) != 12:
        raise ValueError("entity id must be 12 chars")
    base = f"{lou_prefix}00{entity_id12}".upper()
    return base + compute_lei_check_digits(base)


# ── registry records ──
def _unsigned_certificate(kind: str, subject: str, record_id: str) -> dict:
    return {
        "@context": ["https://www.w3.org/ns/credentials/v2"],
        "type": ["VerifiableCredential", kind],
        "credentialSubject": {"id": subject, "record": record_id},
        "proof": None,                                   # G1
        "server_held_authority": SERVER_HELD_AUTHORITY,  # False
        "status": "issued-unsigned",
    }


def register_incorporation(entity_name: str, officers: list, capital: float, articles: str,
                           address: str, jurisdiction: str, sequence: int,
                           lou_prefix: str = "EZHY", entity_id12: str | None = None) -> dict:
    """Validate + construct a company incorporation registration. Pure function.

    Requires a name, ≥1 officer, non-negative capital, articles, an address. Assigns a
    deterministic registry number (jurisdiction + zero-padded sequence) and an ISO 17442 LEI.
    """
    if not entity_name:
        raise ValueError("incorporation: entity_name required")
    if not officers:
        raise ValueError("incorporation: at least one officer required")
    if capital < 0:
        raise ValueError("incorporation: capital must be >= 0")
    if not articles:
        raise ValueError("incorporation: articles required")
    if not address:
        raise ValueError("incorporation: address required")
    if sequence < 0:
        raise ValueError("incorporation: sequence must be >= 0")

    registry_number = f"{jurisdiction.upper()}-{sequence:08d}"
    eid = (entity_id12 or f"{sequence:012d}")[:12].rjust(12, "0").upper()
    lei = assign_lei(lou_prefix, eid)

    record = {
        "record_id": registry_number,
        "kind": "incorporation",
        "entity_name": entity_name,
        "officers": list(officers),
        "capital": capital,
        "jurisdiction": jurisdiction,
        "lei": lei,
        "immutable": True,  # G5
    }
    return {"record": record, "lei": lei, "registry_number": registry_number,
            "certificate": _unsigned_certificate("IncorporationCertificate", registry_number, registry_number)}


def register_change(registry_number: str, changed_fields: dict, effective_date: str) -> dict:
    """Append-only amendment (変更登記). G5: never overwrites the incorporation record."""
    if not registry_number:
        raise ValueError("change: registry_number required")
    if not changed_fields:
        raise ValueError("change: changed_fields required")
    record = {
        "record_id": f"{registry_number}#chg@{effective_date}",
        "kind": "change",
        "registry_number": registry_number,
        "changed": dict(changed_fields),
        "effective_date": effective_date,
        "immutable": True,  # G5 — an amendment is appended, not an overwrite
    }
    return {"record": record}


def append(history: list, result: dict) -> list:
    """G5: append a registry record, returning a NEW list."""
    return list(history) + [result["record"]]


def solve(*_args, **_kwargs):
    raise RuntimeError(
        "corp-registry R0: reference validation + LEI assignment only. Live registration against "
        "a real corporate register is Council+operator gated (principal A: Council Lv7+; "
        "principal B: adopting state)."
    )


if __name__ == "__main__":
    r = register_incorporation("Tree of Life K.K.", ["officer:rin"], 10_000_000,
                               "articles-hash", "東京都新宿区", "JPN", 1)
    print("registry:", r["registry_number"], "LEI:", r["lei"], "valid?", validate_lei(r["lei"]))
