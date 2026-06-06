#!/usr/bin/env python3
"""Tests for the R1.B datom-persistence layer (matsurigoto 政, ADR-2606052300).

Drives the REAL modules to produce outputs, then verifies the EAVT conversion + the structural
invariants (G1 unsigned, G3 authority, G5 append-only, G8 gated). Standalone + pytest.
"""
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "modules"))

import datoms as D            # noqa: E402
import tax_assess as T        # noqa: E402
import civil_registry as C    # noqa: E402
import corp_registry as R     # noqa: E402
import credential_issue as P  # noqa: E402

TX = dict(operated_by=":etzhayyim-council", authority_mode=":sovereign-governance",
          as_of="2026-06-06T00:00:00Z", spec_basis="spec")


def _val(datoms, attr):
    return [v for (_e, a, v) in datoms if a == attr]


def test_tax_assessment_datoms_roundtrip():
    out = T.assess_from_return(6_000_000, 1_000_000, "JPN.income")
    ds = D.assessment_datoms(out, tx_id="t1", service="tax.income.file", **TX)
    assert _val(ds, ":egov.assessment/liability") == [572_500.0]
    assert _val(ds, ":egov.tx/module") == ["tax-assess"]
    assert _val(ds, ":egov.tx/server-held-authority") == [False]  # G1


def test_civil_record_is_immutable_g5():
    out = C.register_birth("b1", "child:a", ["p"], "tokyo", "2026-06-01T00:00:00Z", "2026-06-05T00:00:00Z")
    ds = D.civil_datoms(out, tx_id="t2", service="civil.birth.register", **TX)
    assert _val(ds, ":egov.record/immutable") == [True]   # G5
    assert _val(ds, ":egov.record/kind") == ["birth"]


def test_incorporation_datoms_carry_valid_lei():
    out = R.register_incorporation("Co", ["o"], 0, "art", "addr", "JPN", 1)
    ds = D.incorporation_datoms(out, tx_id="t3", service="corp.incorporation.register", **TX)
    lei = _val(ds, ":egov.record/lei")[0]
    assert R.validate_lei(lei)                              # the persisted LEI is valid
    assert _val(ds, ":egov.record/immutable") == [True]


def test_passport_datoms_certificate_unsigned_g1():
    out = P.issue_passport("L898902C3", "UTO", "UTO", "ERIKSSON", "ANNA", "740812", "F", "120415", "did:x")
    ds = D.passport_datoms(out, tx_id="t4", service="passport.issue", **TX)
    assert _val(ds, ":egov.cert/proof") == [None]          # G1 — unsigned on the log
    assert _val(ds, ":egov.cert/status") == ["issued-unsigned"]


def test_g1_rejects_a_signed_artifact():
    out = T.assess_from_return(1_000_000, 0, "FLAT20.income")
    out["receipt"]["proof"] = "forged-sig"                 # simulate a signed artifact
    try:
        D.assessment_datoms(out, tx_id="t5", service="tax.income.file", **TX)
    except ValueError:
        return
    raise AssertionError("G1: a signed module artifact must be rejected")


def test_g3_rejects_unknown_operator():
    out = T.assess_from_return(1_000_000, 0, "FLAT20.income")
    bad = dict(TX); bad["operated_by"] = ":the-platform"
    try:
        D.assessment_datoms(out, tx_id="t6", service="tax.income.file", **bad)
    except ValueError:
        return
    raise AssertionError("G3: an illegitimate operator must be rejected")


def test_g3_both_principals_accepted():
    out = T.assess_from_return(1_000_000, 0, "FLAT20.income")
    a = D.assessment_datoms(out, tx_id="ta", service="s",
                            operated_by=":etzhayyim-council", authority_mode=":sovereign-governance",
                            as_of="2026-06-06T00:00:00Z", spec_basis="x")
    b = D.assessment_datoms(out, tx_id="tb", service="s",
                            operated_by=":adopting-government", authority_mode=":supplied-to-state",
                            as_of="2026-06-06T00:00:00Z", spec_basis="x")
    assert _val(a, ":egov.tx/operated-by") == [":etzhayyim-council"]
    assert _val(b, ":egov.tx/operated-by") == [":adopting-government"]


def test_g2_requires_spec_basis():
    out = T.assess_from_return(1_000_000, 0, "FLAT20.income")
    bad = dict(TX); bad["spec_basis"] = ""
    try:
        D.assessment_datoms(out, tx_id="t7", service="s", **bad)
    except ValueError:
        return
    raise AssertionError("G2: empty spec-basis must be rejected")


def test_ingest_batch_dry_run_body():
    out = T.assess_from_return(1_000_000, 0, "FLAT20.income")
    ds = D.assessment_datoms(out, tx_id="t8", service="s", **TX)
    body = D.kg_ingest_batch(ds)
    assert body["op"] == "kg.ingest_batch"
    assert body["published"] is False
    assert body["count"] == len(ds)


def test_g8_live_publish_is_gated():
    try:
        D.kg_ingest_batch([], published=True)
    except RuntimeError:
        return
    raise AssertionError("G8: published=True must raise (Council+operator gated)")


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} passed")
    return 0


if __name__ == "__main__":
    sys.exit(_run())
