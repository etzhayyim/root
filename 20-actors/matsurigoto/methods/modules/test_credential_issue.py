#!/usr/bin/env python3
"""Conformance tests for the credential-issue module (matsurigoto 政, ADR-2606052300).

The check-digit tests reproduce the published ICAO Doc 9303 worked examples exactly:
  doc number L898902C3 → 6 ; DOB 740812 → 2 ; expiry 120415 → 9
and the full UTOPIA/ERIKSSON specimen line-2. Standalone + pytest.
"""
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import credential_issue as P  # noqa: E402

# canonical ICAO 9303 specimen line 2
SPECIMEN_L2 = "L898902C36UTO7408122F1204159ZE184226B<<<<<10"


def test_no_server_authority_document_unsigned():
    """G1 — SOD/proof unsigned; the issuing state signs with its ICAO-PKD key."""
    assert P.SERVER_HELD_AUTHORITY is False
    p = P.issue_passport("L898902C3", "UTO", "UTO", "ERIKSSON", "ANNA MARIA",
                         "740812", "F", "120415", "did:web:x", "ZE184226B")
    assert p["document"]["sod"] is None
    assert p["document"]["proof"] is None


def test_icao_doc_number_check_digit():
    """ICAO 9303 example: L898902C3 → 6."""
    assert P.mrz_check_digit("L898902C3") == "6"


def test_icao_dob_check_digit():
    """ICAO 9303 example: 740812 → 2."""
    assert P.mrz_check_digit("740812") == "2"


def test_icao_expiry_check_digit():
    """ICAO 9303 example: 120415 → 9."""
    assert P.mrz_check_digit("120415") == "9"


def test_filler_value_zero():
    assert P.mrz_check_digit("<<<<<<") == "0"


def test_full_specimen_line2_reproduced():
    """The complete UTOPIA / ERIKSSON ANNA MARIA TD3 line 2 is reproduced exactly."""
    mrz = P.build_td3_mrz("L898902C3", "UTO", "UTO", "ERIKSSON", "ANNA MARIA",
                          "740812", "F", "120415", "ZE184226B")
    assert mrz["line2"] == SPECIMEN_L2
    assert len(mrz["line2"]) == 44


def test_specimen_line1():
    mrz = P.build_td3_mrz("L898902C3", "UTO", "UTO", "ERIKSSON", "ANNA MARIA",
                          "740812", "F", "120415", "ZE184226B")
    assert mrz["line1"] == "P<UTOERIKSSON<<ANNA<MARIA" + "<" * (44 - len("P<UTOERIKSSON<<ANNA<MARIA"))
    assert len(mrz["line1"]) == 44


def test_validate_specimen_passes():
    assert P.validate_td3_line2(SPECIMEN_L2) is True


def test_validate_detects_corruption():
    bad = list(SPECIMEN_L2)
    bad[0] = "X" if bad[0] != "X" else "Y"
    assert P.validate_td3_line2("".join(bad)) is False


def test_validate_rejects_wrong_length():
    assert P.validate_td3_line2("TOO SHORT") is False


def test_roundtrip_arbitrary_passport_validates():
    p = P.issue_passport("AB1234567", "JPN", "JPN", "YAMADA", "TARO",
                         "900101", "M", "300101", "did:web:etz")
    assert P.validate_td3_line2(p["mrz"]["line2"]) is True


def test_bad_country_code_raises():
    try:
        P.build_td3_mrz("X", "JP", "JPN", "A", "B", "900101", "M", "300101")
    except ValueError:
        return
    raise AssertionError("2-letter country code must raise")


def test_solve_is_gated_at_r0():
    try:
        P.solve()
    except RuntimeError:
        return
    raise AssertionError("solve() must raise at R0")


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} passed")
    return 0


if __name__ == "__main__":
    sys.exit(_run())
