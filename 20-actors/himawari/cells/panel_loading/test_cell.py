#!/usr/bin/env python3
"""himawari 向日葵 panel_loading — cell logic tests (ADR-2606021200).

Pure-logic tests over PanelLoadingCell.solve; no kotoba host bindings required
(the datalog import degrades to None in local dev). Verifies the constitutional
invariants of the 積込 cell, which COMPOSES the sarutahiko F10 LoaderRobot
(ADR-2606013100) and does NOT re-implement loader physics:

  - emits an com.etzhayyim.himawari.loadingRecord with all required fields
  - palletizes module serials at the loader tray capacity (pure arithmetic)
  - G12: refuses a non-internal carrier (internal hikari install only)
  - G7: logs displaced human tasks to a Liberation-Metric CID (never omitted)
  - composes the F10 LoadPhase outcome; rejects invented phases; flags completion
"""
import importlib.util
import json
import pathlib

# Load the sibling cell.py under a UNIQUE module name so `pytest cells/` can collect
# this file without the bare module name `cell` colliding across the 6 sibling
# cell.py files. The standalone `__main__` runner below works unchanged.
_spec = importlib.util.spec_from_file_location(
    "himawari_panel_loading_cell", pathlib.Path(__file__).parent / "cell.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
PanelLoadingCell = _mod.PanelLoadingCell

# Matching lexicon for the conformance test (load required + #def shapes from SSoT).
_LEXICON_PATH = (
    pathlib.Path(__file__).resolve().parents[4]
    / "00-contracts/lexicons/com/etzhayyim/himawari/loadingRecord.json"
)


def _base_state(**overrides) -> dict:
    st = {
        "loadingId": "load-2026-0602-001",
        "recordedAt": "2026-06-02T09:30:00Z",
        "moduleSerials": [f"HMW-MOD-{i:04d}" for i in range(1, 73)],  # 72 modules
        "carrierDid": "did:web:etzhayyim.com:hikari#carrier-01",
        "carrierInternal": True,
        "loaderPhase": "Done",
        "palletCapacity": 36,
        "humanTasksRemoved": ["manual-pallet-stack", "forklift-drive", "strap-tie-down"],
    }
    st.update(overrides)
    return st


# JSON-schema-ish type → python type(s) for the conformance assertions.
_TYPE_MAP = {
    "string": str,
    "integer": int,
    "boolean": bool,
    "array": list,
    "object": dict,
}


def test_emits_loading_record_with_required_fields():
    out = PanelLoadingCell().solve(_base_state())
    rec = out["loadingRecord"]
    assert rec is not None
    assert rec["$type"] == "com.etzhayyim.himawari.loadingRecord"
    for field in ("loadingId", "moduleSerials", "carrierDid", "loaderRobotDid"):
        assert field in rec and rec[field], f"required lexicon field {field} missing/empty"
    assert rec["moduleSerials"][0] == "HMW-MOD-0001"


def test_palletizes_at_tray_capacity():
    # 72 modules / 36 per pallet = exactly 2 pallets
    out = PanelLoadingCell().solve(_base_state())
    assert out["loadingRecord"]["palletCount"] == 2
    # 73 modules / 36 = 3 pallets (ceil)
    serials = [f"HMW-MOD-{i:04d}" for i in range(1, 74)]
    out2 = PanelLoadingCell().solve(_base_state(moduleSerials=serials))
    assert out2["loadingRecord"]["palletCount"] == 3


def test_g12_refuses_non_internal_carrier():
    out = PanelLoadingCell().solve(_base_state(carrierInternal=False))
    assert out["refused"] is True
    assert out["loadingRecord"] is None
    assert "G12" in out["reason"]


def test_g12_allows_internal_carrier():
    out = PanelLoadingCell().solve(_base_state(carrierInternal=True))
    assert out["refused"] is False
    assert out["loadingRecord"] is not None


def test_g7_liberation_cid_always_present():
    # even an automated cycle that displaced no logged task gets a CID, never omitted
    out = PanelLoadingCell().solve(_base_state(humanTasksRemoved=[]))
    rec = out["loadingRecord"]
    assert rec["humanTasksRemovedCid"], "G7: Liberation-Metric CID must never be omitted"
    assert rec["humanTasksRemovedCid"].startswith("bafyhimawari")


def test_g7_liberation_cid_is_deterministic():
    a = PanelLoadingCell().solve(_base_state())["loadingRecord"]["humanTasksRemovedCid"]
    b = PanelLoadingCell().solve(_base_state())["loadingRecord"]["humanTasksRemovedCid"]
    assert a == b, "same cycle must content-address to the same anchor"


def test_composes_f10_loader_did_default():
    out = PanelLoadingCell().solve(_base_state(loaderRobotDid=None))
    # defaults to the composed sarutahiko F10 lineage — himawari does not invent one
    assert out["loadingRecord"]["loaderRobotDid"] == "did:web:etzhayyim.com:sarutahiko#F10-loader"


def test_completion_reflects_loader_phase():
    done = PanelLoadingCell().solve(_base_state(loaderPhase="Done"))
    assert done["cycleComplete"] is True
    mid = PanelLoadingCell().solve(_base_state(loaderPhase="Carry"))
    assert mid["cycleComplete"] is False  # mid-cycle composed phase, record still emitted
    assert mid["loadingRecord"] is not None


def test_rejects_invented_loader_phase():
    try:
        PanelLoadingCell().solve(_base_state(loaderPhase="Teleport"))
        assert False, "must reject phases not in the composed LoaderRobot LoadPhase enum"
    except ValueError as e:
        assert "LoadPhase" in str(e)


def test_requires_loading_id_and_modules():
    for bad in ({"loadingId": ""}, {"moduleSerials": []}, {"carrierDid": ""}):
        try:
            PanelLoadingCell().solve(_base_state(**bad))
            assert False, f"missing required input {bad} must raise"
        except ValueError:
            pass


def test_recorded_at_passthrough():
    # recordedAt is threaded through from input (deterministic; no wall-clock read).
    out = PanelLoadingCell().solve(_base_state(recordedAt="2026-06-02T11:11:11Z"))
    assert out["loadingRecord"]["recordedAt"] == "2026-06-02T11:11:11Z"


def test_attesting_robots_are_signature_objects():
    out = PanelLoadingCell().solve(_base_state())
    robots = out["loadingRecord"]["attestingRobots"]
    assert isinstance(robots, list) and len(robots) >= 1  # minItems 1
    # mandatory >=1 witness is the composed F10 loader, as a #robotSignature OBJECT
    loader = robots[0]
    assert isinstance(loader, dict), "attestingRobots must be objects, not DID strings"
    assert loader["robotDid"] == "did:web:etzhayyim.com:sarutahiko#F10-loader"
    assert loader["signature"], "#robotSignature.signature is required"
    # caller-supplied extra witnesses are normalized to objects too
    out2 = PanelLoadingCell().solve(
        _base_state(
            attestingRobots=[
                {"robotDid": "did:web:etzhayyim.com:himawari#mimi-01", "role": "mass-check"}
            ]
        )
    )
    extra = out2["loadingRecord"]["attestingRobots"]
    assert any(r["robotDid"].endswith("mimi-01") and r["signature"] for r in extra)


def test_lexicon_conformance_required_fields_and_shapes():
    """Assert the emitted record carries EVERY lexicon-required field with the
    correct type/shape, including the #robotSignature array element shape."""
    lex = json.loads(_LEXICON_PATH.read_text())
    main = lex["defs"]["main"]["record"]
    props = main["properties"]
    required = main["required"]

    rec = PanelLoadingCell().solve(_base_state())["loadingRecord"]

    for field in required:
        assert field in rec, f"lexicon-required field {field!r} missing from record"
        expected = _TYPE_MAP.get(props[field]["type"])
        if expected is not None:
            assert isinstance(rec[field], expected), (
                f"{field!r} must be {props[field]['type']}, got {type(rec[field]).__name__}"
            )
        if props[field]["type"] == "array":
            assert len(rec[field]) >= props[field].get("minItems", 0), (
                f"{field!r} violates minItems {props[field].get('minItems')}"
            )

    # attestingRobots is a ref array of #robotSignature: assert element shape against
    # the #def's own required fields, proving objects (not flat strings) are emitted.
    sig_props = lex["defs"]["robotSignature"]["properties"]
    sig_required = lex["defs"]["robotSignature"]["required"]
    robots = rec["attestingRobots"]
    assert isinstance(robots, list) and len(robots) >= props["attestingRobots"]["minItems"]
    for sig in robots:
        assert isinstance(sig, dict), "#robotSignature elements must be objects"
        for sf in sig_required:
            assert sf in sig and sig[sf], f"#robotSignature required {sf!r} missing/empty"
            assert isinstance(sig[sf], _TYPE_MAP[sig_props[sf]["type"]])


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
