#!/usr/bin/env python3
"""Tests for the himotoki 繙き disclosure-request generator (methods/request.py).

    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_request.py
    python3 test_request.py

Proves every charter gate fires: G3 own-data-only DSAR, G4 true-requester/no-pretext,
G6 PII-as-encrypted-envelope (never plaintext), G8 no mass-filing, G14 verify-before-
dispatch, G10 outbound-gated. himotoki is active but consent-bound and outbound-gated.
"""
from __future__ import annotations

import pathlib
import sys

try:
    from request import (MAX_BATCH, build_batch, build_request, can_dispatch, is_dsar,
                        load_registry, render_edn)
except ImportError:
    from himotoki.methods.request import (  # type: ignore
        MAX_BATCH, build_batch, build_request, can_dispatch, is_dsar, load_registry, render_edn)

_REG = load_registry()
_MEMBER = {"requesterDid": "did:web:etzhayyim.com:member:alice", "ownDataOnly": True,
           "subjectEnvelopeRef": "com.etzhayyim.encrypted:env:alice"}


def _a_dsar_target():
    return next(t for t in _REG.values() if is_dsar(t))


def test_registry_loads_with_stable_ids():
    assert _REG and "Discord Inc.:ccpa-110" in _REG


def test_dsar_classification():
    assert is_dsar({"regime": "ccpa-110"}) and is_dsar({"regime": "gdpr-15"})
    assert is_dsar({"regime": "appi-33"})
    assert not is_dsar({"regime": "us-foia"})


def test_dsar_requires_own_data_only_g3():
    t = _a_dsar_target()
    bad = dict(_MEMBER, ownDataOnly=False)
    try:
        build_request(t, bad); raised = False
    except ValueError as e:
        raised = "G3" in str(e)
    assert raised


def test_request_requires_true_requester_g4():
    t = _a_dsar_target()
    try:
        build_request(t, {"ownDataOnly": True, "subjectEnvelopeRef": "com.etzhayyim.encrypted:env:x"})
        raised = False
    except ValueError as e:
        raised = "G4" in str(e)
    assert raised


def test_pretext_field_refused_g4():
    t = _a_dsar_target()
    bad = dict(_MEMBER, sockpuppet="fake-alice")
    try:
        build_request(t, bad); raised = False
    except ValueError as e:
        raised = "G4" in str(e)
    assert raised


def test_plaintext_pii_refused_g6():
    t = _a_dsar_target()
    bad = dict(_MEMBER, email="alice@example.com")
    try:
        build_request(t, bad); raised = False
    except ValueError as e:
        raised = "G6" in str(e)
    assert raised


def test_non_envelope_subject_ref_refused_g6():
    t = _a_dsar_target()
    bad = dict(_MEMBER, subjectEnvelopeRef="alice plaintext")
    try:
        build_request(t, bad); raised = False
    except ValueError as e:
        raised = "G6" in str(e)
    assert raised


def test_valid_draft_carries_envelope_not_plaintext():
    d = build_request(_a_dsar_target(), _MEMBER)
    assert d["subjectEnvelopeRef"].startswith("com.etzhayyim.encrypted:")
    assert "name" not in d and "email" not in d and d["dispatchReady"] is False


def test_dispatch_refused_against_unverified_target_g14():
    t = _a_dsar_target()                                  # all seed targets are unverified
    allowed, reason = can_dispatch(t, operator_gate=True)
    assert allowed is False and "G14" in reason


def test_dispatch_refused_without_operator_gate_g10():
    t = dict(_a_dsar_target(), verificationStatus="verified")
    allowed, reason = can_dispatch(t, operator_gate=False)
    assert allowed is False and "G10" in reason


def test_dispatch_allowed_when_verified_and_gated():
    t = dict(_a_dsar_target(), verificationStatus="verified")
    allowed, _ = can_dispatch(t, operator_gate=True)
    assert allowed is True


def test_mass_filing_refused_g8():
    ids = list(_REG)[: MAX_BATCH + 1]
    try:
        build_batch(ids, _MEMBER, _REG); raised = False
    except ValueError as e:
        raised = "G8" in str(e)
    assert raised


def test_render_edn_marks_invariants():
    edn = render_edn([build_request(_a_dsar_target(), _MEMBER)])
    assert ":himotoki.req/own-data-only" in edn and ":himotoki.req/dispatch-ready false" in edn
    assert "encrypted" in edn and "gated" in edn


def _run():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"himotoki request.py: {len(fns)}/{len(fns)} tests passed")
    return True


if __name__ == "__main__":
    sys.exit(0 if _run() else 1)
