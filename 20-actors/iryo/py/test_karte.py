#!/usr/bin/env python3
"""iryo 医療 — 電子カルテ PHI gate tests."""
import pytest
from karte import (Diagnosis, Insurance, Karte, Patient, PhiLeak, SoapNote,
                   rotating_pseudonym_did)


def _karte():
    return Karte(
        patient=Patient(pseudonym_did="did:web:patient.iryo.etzhayyim.com:abc123",
                        sex="M", birth_year=1980, encrypted_payload_cid="bafy...phi"),
        insurance=Insurance(hokensha_bango="01130012", futan_wari=0.3),
        diagnoses=[Diagnosis("4019005", "I10", "高血圧症", onset="2026-01-10",
                             is_main=True)],
    )


def test_public_meta_is_codes_only_no_phi():
    meta = _karte().public_meta()
    # no plaintext PHI keys leak
    Karte.assert_no_phi(meta)
    assert meta["patientDid"].startswith("did:web:")
    assert meta["diagnoses"][0]["icd10"] == "I10"
    assert "name" not in meta and "dob" not in meta


def test_assert_no_phi_rejects_smuggled_plaintext():
    bad = {"patientDid": "did:..", "name": "山田太郎"}
    with pytest.raises(PhiLeak):
        Karte.assert_no_phi(bad)


def test_assert_no_phi_rejects_phi_in_diagnosis():
    bad = {"diagnoses": [{"icd10": "I10", "note": "本人談: ..."}]}
    with pytest.raises(PhiLeak):
        Karte.assert_no_phi(bad)


def test_soap_note_requires_encrypted_cid():
    with pytest.raises(PhiLeak):
        SoapNote(encounter_date="2026-06-07", author_did="did:web:dr", encrypted_cid="")
    ok = SoapNote(encounter_date="2026-06-07", author_did="did:web:dr",
                  encrypted_cid="bafy...soap")
    assert ok.encrypted_cid


def test_rotating_pseudonym_changes_per_period():
    a = rotating_pseudonym_did("patient-secret", "2026-06")
    b = rotating_pseudonym_did("patient-secret", "2026-07")
    assert a != b
    assert a == rotating_pseudonym_did("patient-secret", "2026-06")  # deterministic
    assert a.startswith("did:web:patient.iryo.etzhayyim.com:")


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-q"]))
