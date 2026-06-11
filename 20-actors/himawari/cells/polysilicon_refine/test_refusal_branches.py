#!/usr/bin/env python3
"""polysilicon_refine — G2 refusal-branch coverage (ADR-2606021200 / R1 maturation).

test_cell.py covers the headline XUAR/conflict-mineral/logic-grade refusals but
left several constitutional G2 validation branches in solve() uncovered:

  - missing lotId            (no anonymous feedstock, G2)
  - unknown refining process (must be a known solar-grade process)
  - empty declaredOrigin     (required for XUAR-exclusion screening, G2)
  - robot-signature auto-fill (a #robotSignature lacking `signature` is completed
                               deterministically rather than dropped, G11)

Each is a structural anchor of the actor; this file pins them with focused tests.
"""
import importlib.util
import pathlib

_spec = importlib.util.spec_from_file_location(
    "himawari_polysilicon_refine_cell_r", pathlib.Path(__file__).parent / "cell.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

_CLEAN = {
    "lotId": "POLY-2026-000123",
    "recordedAt": "2026-06-02T00:00:00Z",
    "feedstockGrade": "solar-grade-6N",
    "process": "fbr",
    "declaredOrigin": "Trondheim, Norway",
    "supplierDid": "did:web:example-poly.no",
    "originRegionAttestationCid": "bafyabc-origin",
    "sourcingAuditCid": "bafyabc-audit",
    "attestingEngineerDid": "did:plc:pv-engineer-001",
    "attestingRobots": ["kuni-umi:mimi", "kuni-umi:otete"],
    "embodiedEnergyWhPerKg": 80000,
}


def _solve(over):
    return _mod.PolysiliconRefineCell().solve({**_CLEAN, **over})


def test_missing_lot_id_refused():
    out = _solve({"lotId": ""})
    assert out["accepted"] is False
    assert any("lotId is required" in v for v in out["violations"])
    assert out["routeToCell"] is None


def test_unknown_process_refused():
    out = _solve({"process": "alchemy-9000"})
    assert out["accepted"] is False
    assert any("process" in v and "unknown" in v for v in out["violations"])


def test_empty_declared_origin_refused():
    out = _solve({"declaredOrigin": ""})
    assert out["accepted"] is False
    assert any("declaredOrigin is required" in v for v in out["violations"])


def test_robot_signature_autofilled_when_missing():
    # #robotSignature objects lacking `signature` must be completed deterministically
    # (G11 quorum), not silently dropped — a clean lot still accepts.
    out = _solve(
        {
            "attestingRobots": [
                {"robotDid": "kuni-umi:mimi"},
                {"robotDid": "kuni-umi:otete"},
            ]
        }
    )
    robots = out["provenance"]["attestingRobots"]
    assert len(robots) == 2
    for sig in robots:
        assert sig["robotDid"]
        assert sig["signature"], "missing signature must be auto-filled, not empty"
    assert out["accepted"] is True


if __name__ == "__main__":
    import sys

    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"  ok   {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL {fn.__name__}: {e}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
