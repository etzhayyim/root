#!/usr/bin/env python3
"""matsurigoto 政 — `credential-issue` module (R0 reference implementation).

ADR-2606052300. Fourth executable vertical slice: travel-document / ID-credential engine
behind `passport.issue` / `passport.renew` / `id.national.issue` — i.e. パスポート発行.

WHAT IT IS: a pure-function ICAO Doc 9303 **TD3 MRZ** (Machine Readable Zone) builder with the
real **7-3-1 weighted check-digit** algorithm — the conformance anchor of this module. The ICAO
9303 worked example `L898902C3` → check digit `6` and DOB `740812` → `2` are reproduced exactly
(see tests). Produces the MRZ + an UNSIGNED issuance record (the passport authority signs the
chip/SOD with ITS own ICAO-PKD key — never this module, G1).

Spec basis (G2): ICAO Doc 9303 (MRTD) + ISO/IEC 19794 (biometrics, referenced) + W3C VC 2.0.

Charter invariants:
  G1 no-operator-master-key : SERVER_HELD_AUTHORITY False; the document is UNSIGNED here (the
                              issuing state signs the SOD with its ICAO-PKD CSCA/DS key).
  G2 spec-derived-only      : ICAO 9303 MRZ structure + 7-3-1 check digit.
  G6 data-minimization      : only MRZ fields; no biometric template stored in this reference.

stdlib only, no I/O, no network. Importable as a kotoba-wasm module contract.
"""
from __future__ import annotations

SERVER_HELD_AUTHORITY = False  # G1

_WEIGHTS = (7, 3, 1)


def _char_value(ch: str) -> int:
    """ICAO 9303 MRZ char value: digits = value, A-Z = 10..35, filler '<' = 0."""
    if ch == "<":
        return 0
    if ch.isdigit():
        return int(ch)
    if "A" <= ch <= "Z":
        return ord(ch) - 55  # 'A' → 10
    raise ValueError(f"MRZ char must be [0-9A-Z<], got {ch!r}")


def mrz_check_digit(data: str) -> str:
    """ICAO Doc 9303 check digit: Σ(value × weight[7,3,1 repeating]) mod 10."""
    total = sum(_char_value(ch) * _WEIGHTS[i % 3] for i, ch in enumerate(data))
    return str(total % 10)


def _pad(s: str, n: int) -> str:
    """Uppercase, replace spaces with filler '<', pad/truncate to n chars."""
    s = s.upper().replace(" ", "<")
    return (s + "<" * n)[:n]


def build_td3_mrz(doc_number: str, issuing_state: str, nationality: str, surname: str,
                  given_names: str, dob_yymmdd: str, sex: str, expiry_yymmdd: str,
                  personal_number: str = "") -> dict:
    """Build the two 44-char TD3 (passport) MRZ lines with all ICAO check digits."""
    if len(issuing_state) != 3 or len(nationality) != 3:
        raise ValueError("issuing_state and nationality must be 3-letter ICAO codes")
    if len(dob_yymmdd) != 6 or len(expiry_yymmdd) != 6:
        raise ValueError("dates must be YYMMDD (6 digits)")
    if sex not in ("M", "F", "<"):
        raise ValueError("sex must be M, F, or < (unspecified)")

    name_field = _pad(f"{surname}<<{given_names}", 39)
    line1 = f"P<{issuing_state.upper()}{name_field}"

    doc = _pad(doc_number, 9)
    c_doc = mrz_check_digit(doc)
    c_dob = mrz_check_digit(dob_yymmdd)
    c_exp = mrz_check_digit(expiry_yymmdd)
    pers = _pad(personal_number, 14)
    c_pers = mrz_check_digit(pers)
    composite_input = doc + c_doc + dob_yymmdd + c_dob + expiry_yymmdd + c_exp + pers + c_pers
    c_composite = mrz_check_digit(composite_input)

    line2 = (f"{doc}{c_doc}{nationality.upper()}{dob_yymmdd}{c_dob}{sex}"
             f"{expiry_yymmdd}{c_exp}{pers}{c_pers}{c_composite}")
    return {"line1": line1, "line2": line2,
            "check_digits": {"doc": c_doc, "dob": c_dob, "expiry": c_exp,
                             "personal": c_pers, "composite": c_composite}}


def validate_td3_line2(line2: str) -> bool:
    """Verify the field + composite check digits of a TD3 MRZ line 2."""
    if len(line2) != 44:
        return False
    try:
        doc, c_doc = line2[0:9], line2[9]
        dob, c_dob = line2[13:19], line2[19]
        exp, c_exp = line2[21:27], line2[27]
        pers, c_pers = line2[28:42], line2[42]
        c_comp = line2[43]
        if mrz_check_digit(doc) != c_doc:
            return False
        if mrz_check_digit(dob) != c_dob:
            return False
        if mrz_check_digit(exp) != c_exp:
            return False
        if mrz_check_digit(pers) != c_pers:
            return False
        composite_input = doc + c_doc + dob + c_dob + exp + c_exp + pers + c_pers
        return mrz_check_digit(composite_input) == c_comp
    except ValueError:
        return False


def _unsigned_document(kind: str, subject: str, mrz: dict) -> dict:
    return {
        "type": ["VerifiableCredential", kind],
        "credentialSubject": {"id": subject},
        "mrz": mrz,
        "sod": None,                                     # G1 — issuing state signs the SOD (ICAO PKD)
        "proof": None,
        "server_held_authority": SERVER_HELD_AUTHORITY,  # False
        "status": "issued-unsigned",
    }


def issue_passport(doc_number: str, issuing_state: str, nationality: str, surname: str,
                   given_names: str, dob_yymmdd: str, sex: str, expiry_yymmdd: str,
                   subject_did: str, personal_number: str = "") -> dict:
    """Validate + assemble an MRTD passport (ICAO 9303). Returns MRZ + unsigned document (G1)."""
    if not doc_number:
        raise ValueError("passport: doc_number required")
    if not surname:
        raise ValueError("passport: surname required")
    mrz = build_td3_mrz(doc_number, issuing_state, nationality, surname, given_names,
                        dob_yymmdd, sex, expiry_yymmdd, personal_number)
    return {"mrz": mrz, "document": _unsigned_document("Passport", subject_did, mrz)}


def solve(*_args, **_kwargs):
    raise RuntimeError(
        "credential-issue R0: reference MRZ assembly only. Live passport/ID issuance + SOD signing "
        "is the issuing state's ICAO-PKD authority (principal B) / Council Lv7+ (principal A) + "
        "operator gated."
    )


if __name__ == "__main__":
    p = issue_passport("L898902C3", "UTO", "UTO", "ERIKSSON", "ANNA MARIA",
                       "740812", "F", "120415", "did:web:example", personal_number="ZE184226B")
    print("MRZ L2:", p["mrz"]["line2"], "valid?", validate_td3_line2(p["mrz"]["line2"]))
