#!/usr/bin/env python3
"""Structural charter-invariant tests for 助 (tasuke) — ADR-2606060900.

Assert the invariants STRUCTURALLY over the parsed ontology / lexicons / code constants — not by
grepping prose. The load-bearing trio: G1 全て無料 (fee unrepresentable), G2 本人作成・本人提出
(no 代理), G3 警察authored不可 (member-authored only). Plus G5 (no paid referral), G6 (PII by
ref), G7 (no-server-key), G9 (draft-only).
"""
from __future__ import annotations

import pathlib

from _edn import load_edn

_ROOT = pathlib.Path(__file__).resolve().parents[1]
_LEX = _ROOT / "lex"
_ONTOLOGY = _ROOT.parents[1] / "00-contracts" / "schemas" / "cybercrime-victim-support-ontology.kotoba.edn"


def _onto():
    return load_edn(_ONTOLOGY)


def _props(lex_name: str) -> dict:
    d = load_edn(_LEX / f"{lex_name}.edn")
    return d[":defs"][":main"][":record"][":properties"]


def _allowed(ident: str):
    for m in _onto()[":schema"]:
        if isinstance(m, dict) and m.get(":db/ident") == ident:
            return m.get(":db/allowed")
    return None


# ── G1 全て無料 — cost is structurally 0 in ontology + lexicons + code ────────
def test_ontology_support_cost_allowed_zero_only():
    assert _allowed(":support/cost-jpy") == [0]


def test_intake_lexicon_cost_const_zero():
    assert _props("victimIntake")[":supportCostJpy"].get(":const") == 0


def test_supportcase_lexicon_cost_const_zero():
    assert _props("supportCase")[":supportCostJpy"].get(":const") == 0


def test_code_support_cost_is_zero():
    from triage import SUPPORT_COST_JPY, support_cost_jpy
    assert SUPPORT_COST_JPY == 0 and support_cost_jpy() == 0


# ── G3 警察authored不可 — doc author is member-only ──────────────────────────
def test_ontology_doc_authors_member_only():
    assert _onto()[":ontology/doc-authors"] == [":member"]
    assert _allowed(":doc/authored-by") == [":member"]


def test_police_report_lexicon_author_const_member():
    assert _props("policeReportDraft")[":authoredBy"].get(":const") == "member"


def test_doc_authors_exclude_police_official_server():
    authors = _onto()[":ontology/doc-authors"]
    for forbidden in (":police", ":official", ":server"):
        assert forbidden not in authors


# ── G2 本人作成・本人提出 — support-role has no 代理 ─────────────────────────
def test_ontology_support_roles_exclude_representation():
    roles = _onto()[":ontology/support-roles"]
    assert roles == [":guide", ":draft-assist", ":self-submit"]
    for forbidden in (":represent", ":proxy-submit", ":agent-file"):
        assert forbidden not in roles


def test_recovery_lexicon_role_enum_excludes_representation():
    enum = set(_props("recoveryPlan")[":supportRole"].get(":enum", []))
    assert enum == {"guide", "draft-assist", "self-submit"}
    assert enum.isdisjoint({"represent", "proxy-submit", "agent-file"})


def test_docs_need_member_signature_const_true():
    for lex in ("policeReportDraft", "platformRequest"):
        assert _props(lex)[":needsMemberSignature"].get(":const") is True


# ── G5 no paid counsel ───────────────────────────────────────────────────────
def test_ontology_referral_paid_allowed_false_only():
    assert _allowed(":referral/paid") == [False]
    assert _allowed(":support/paid-referral") == [False]


def test_supportcase_paid_referral_const_false():
    assert _props("supportCase")[":paidReferral"].get(":const") is False


# ── G6 PII-by-reference — evidence has no plaintext field ────────────────────
def test_evidence_lexicon_has_no_plaintext_field():
    props = _props("evidenceItem")
    assert not any("plaintext" in str(k).lower() or "raw" in str(k).lower() for k in props)
    assert ":envelopeRef" in props


# ── G7 no-server-key ─────────────────────────────────────────────────────────
def test_intake_server_held_key_const_false():
    assert _props("victimIntake")[":serverHeldKey"].get(":const") is False


def test_ontology_server_held_key_allowed_false():
    assert _allowed(":case/server-held-key") == [False]


# ── G9 draft-only at R0 ──────────────────────────────────────────────────────
def test_doc_published_allowed_false():
    assert _allowed(":doc/published") == [False]
    for lex in ("policeReportDraft", "platformRequest", "recoveryPlan"):
        assert _props(lex)[":published"].get(":const") is False


# ── code ≡ ontology vocab ────────────────────────────────────────────────────
def test_code_scam_kinds_match_ontology():
    from triage import SCAM_KINDS
    onto = {k.lstrip(":") for k in _onto()[":ontology/scam-kinds"]}
    assert set(SCAM_KINDS) == onto


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
    print(f"{len(fns) - failed}/{len(fns)} passed in test_charter_invariants.py")
    sys.exit(1 if failed else 0)
