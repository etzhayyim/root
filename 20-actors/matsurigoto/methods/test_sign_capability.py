#!/usr/bin/env python3
"""Tests for the R1.C sign/authority layer (matsurigoto 政, ADR-2606052300 + 2605231525)."""
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "modules"))

import sign_capability as S  # noqa: E402
import tax_assess as T       # noqa: E402

COUNCIL = "did:web:etzhayyim.com:council:safe"
STATE = "did:web:gov.example:tax-authority"
AT = "2026-06-06T00:00:00Z"


def _unsigned():
    return T.assess_from_return(1_000_000, 0, "FLAT20.income")["receipt"]


def test_module_holds_no_key():
    assert S.SIGNER_HELD_PRIVATE_KEY is False


def test_server_side_signing_always_raises():
    """The structural no-server-key guarantee."""
    try:
        S.sign_server_side(_unsigned())
    except RuntimeError:
        return
    raise AssertionError("sign_server_side must raise (no-server-key)")


def test_principal_a_council_signs():
    signed = S.attach_external_proof(_unsigned(), signer_did=COUNCIL,
                                     authority_mode=":sovereign-governance",
                                     signature="0xSAFE", signed_at=AT)
    assert signed["proof"]["signer_did"] == COUNCIL
    assert "unsigned" not in signed["status"]
    assert S.verify_proof(signed) is True


def test_principal_b_state_signs_with_own_key():
    signed = S.attach_external_proof(_unsigned(), signer_did=STATE,
                                     authority_mode=":supplied-to-state",
                                     signature="0xSTATE", signed_at=AT)
    assert S.verify_proof(signed) is True


def test_principal_a_rejects_non_council_signer():
    """Sovereign acts must be signed by a Council organ, not an arbitrary did."""
    try:
        S.attach_external_proof(_unsigned(), signer_did=STATE,
                                authority_mode=":sovereign-governance",
                                signature="0xX", signed_at=AT)
    except ValueError:
        return
    raise AssertionError("sovereign act by a non-council signer must raise")


def test_principal_b_rejects_etzhayyim_holding_state_key():
    """etzhayyim never holds the adopting state's key — an etzhayyim did can't sign a state act."""
    try:
        S.attach_external_proof(_unsigned(), signer_did="did:web:etzhayyim.com:worker",
                                authority_mode=":supplied-to-state",
                                signature="0xX", signed_at=AT)
    except ValueError:
        return
    raise AssertionError("etzhayyim signing a supplied-to-state act must raise")


def test_empty_signature_refused():
    try:
        S.attach_external_proof(_unsigned(), signer_did=COUNCIL,
                                authority_mode=":sovereign-governance",
                                signature="", signed_at=AT)
    except ValueError:
        return
    raise AssertionError("empty signature must raise (matsurigoto mints none)")


def test_double_sign_refused():
    signed = S.attach_external_proof(_unsigned(), signer_did=COUNCIL,
                                     authority_mode=":sovereign-governance",
                                     signature="0xSAFE", signed_at=AT)
    try:
        S.attach_external_proof(signed, signer_did=COUNCIL,
                                authority_mode=":sovereign-governance",
                                signature="0xAGAIN", signed_at=AT)
    except ValueError:
        return
    raise AssertionError("re-signing an already-signed artifact must raise")


def test_tampered_payload_fails_verify():
    signed = S.attach_external_proof(_unsigned(), signer_did=COUNCIL,
                                     authority_mode=":sovereign-governance",
                                     signature="0xSAFE", signed_at=AT)
    signed["assessed_amount"] = 999_999   # tamper a SUBSTANTIVE field after signing
    assert S.verify_proof(signed) is False


def test_unsigned_artifact_does_not_verify():
    assert S.verify_proof(_unsigned()) is False


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} passed")
    return 0


if __name__ == "__main__":
    sys.exit(_run())
