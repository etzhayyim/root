#!/usr/bin/env python3
"""Tests for 助 (tasuke) document generation — G3 member-authored, G1 free, G2 signature, G9 draft."""
from __future__ import annotations

import report_gen as rg

_CASE = {
    ":case/id": "c1", ":case/subject": "did:web:etzhayyim.com:member:alice",
    ":case/scam-kind": ":unauthorized-transfer", ":case/loss-jpy": 480000,
    ":case/narrative": "不正送金被害", ":case/occurred-at-text": "2026-06-03",
    ":case/timeline": ["A", "B"], ":case/loss-breakdown": [{":label": "x", ":jpy": 480000}],
}
_EV = [{":evidence/id": "e1", ":evidence/case": "c1", ":evidence/kind": ":screenshot",
        ":evidence/envelope-ref": "ipfs://bafyX", ":evidence/bytes": "abc", ":evidence/captured-at": 1}]

_ALL = [
    rg.damage_report(_CASE), rg.incident_statement(_CASE), rg.damage_calculation(_CASE),
    rg.evidence_index_doc(_CASE, _EV), rg.bank_freeze_request(_CASE),
    rg.platform_request(_CASE), rg.recovery_plan(_CASE, service="Google"),
]


# ── G3 every generated document is member-authored, never police/official ─────
def test_all_docs_member_authored():
    for d in _ALL:
        assert d[":doc/authored-by"] == ":member"
        assert d[":doc/authored-by"] not in (":police", ":official", ":server")


def test_assert_member_authored_passes_for_all():
    for d in _ALL:
        rg.assert_member_authored(d)  # must not raise


def test_assert_rejects_police_authored():
    bad = dict(rg.damage_report(_CASE)); bad[":doc/authored-by"] = ":police"
    try:
        rg.assert_member_authored(bad)
        assert False, "G3 must reject a police-authored doc"
    except ValueError as e:
        assert "G3" in str(e)


# ── G2/G7 every doc needs the member's signature ─────────────────────────────
def test_all_docs_need_member_signature():
    for d in _ALL:
        assert d[":doc/needs-member-signature"] is True


# ── G1 every doc is free ─────────────────────────────────────────────────────
def test_all_docs_free():
    for d in _ALL:
        assert d[":doc/support-cost-jpy"] == 0


# ── G9 every doc is draft-only at R0 ─────────────────────────────────────────
def test_all_docs_unpublished():
    for d in _ALL:
        assert d[":doc/published"] is False


# ── content sanity ───────────────────────────────────────────────────────────
def test_damage_report_has_signature_line_and_loss():
    body = rg.damage_report(_CASE)[":doc/body"]
    assert "被 害 届" in body and "480,000" in body and "署名" in body


def test_bank_request_cites_legal_basis():
    d = rg.bank_freeze_request(_CASE)
    assert "振り込め詐欺救済法" in d[":doc/body"]
    assert d.get("legal_basis", "").startswith("振り込め詐欺救済法")


def test_recovery_plan_is_self_submit():
    d = rg.recovery_plan(_CASE, service="LINE")
    assert d.get("support_role") == ":self-submit"
    assert d.get("steps") and "代理ログイン" in d[":doc/body"]


def test_damage_calculation_sums_breakdown():
    d = rg.damage_calculation({":case/id": "c1",
                               ":case/loss-breakdown": [{":label": "a", ":jpy": 100},
                                                        {":label": "b", ":jpy": 250}]})
    assert d.get("total_jpy") == 350


if __name__ == "__main__":
    import sys
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL {fn.__name__}: {e}")
    print(f"{len(fns) - failed}/{len(fns)} passed in test_report_gen.py")
    sys.exit(1 if failed else 0)
