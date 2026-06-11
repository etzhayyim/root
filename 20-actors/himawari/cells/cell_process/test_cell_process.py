#!/usr/bin/env python3
"""himawari 向日葵 cell_process — cell logic tests (ADR-2606021200).

Pure-logic tests over the CellProcessCell super-step loop; no kotoba host
bindings required. Verifies the constitutional invariants of the solar-grade
c-Si cell line:

  - end-to-end run emits a valid com.etzhayyim.himawari.cellBatchRecord
  - all lexicon-required fields present (batchId, waferBatchId, cellArchitecture,
    gasAbatementCid, attestingRobots ≥2)
  - G3: fluorinated etch/clean gases abated ≥99% DRE or substituted; a
    sub-floor batch with no substitution HALTS (no record emitted)
  - G6: silver-only metallization flagged off the Ag→Cu roadmap; copper /
    ag-cu-hybrid pass clean
  - G11: ≥2 distinct robot witnesses (Otete + Mimi, composed from kuni-umi)
  - flash IV produces an integer median milliwatt-peak (matches lexicon type)

Run directly:  python3 test_cell_process.py
"""

import importlib.util
import json
import pathlib
import sys

# Load the sibling cell.py under a UNIQUE module name so `pytest cells/` can
# collect all six sibling cell.py files without the bare module-name `cell`
# colliding. (The standalone __main__ runner below works regardless.) The module
# is registered in sys.modules before exec so its @dataclass field-type lookups
# (under `from __future__ import annotations`) resolve against itself.
_MOD_NAME = "himawari_cell_process_cell"
_spec = importlib.util.spec_from_file_location(
    _MOD_NAME, pathlib.Path(__file__).parent / "cell.py"
)
cell_mod = importlib.util.module_from_spec(_spec)
sys.modules[_MOD_NAME] = cell_mod
_spec.loader.exec_module(cell_mod)


def _solve(state):
    return cell_mod.CellProcessCell().solve(state)


# ─── happy path: full line, on-roadmap metallization ───

def test_full_run_emits_cell_batch_record():
    out = _solve({"waferBatchId": "wafer-2026-0601-A", "cellArchitecture": "TOPCon", "metallization": "ag-cu-hybrid"})
    assert "cell_batch_record" in out, "expected a cellBatchRecord on the happy path"
    rec = out["cell_batch_record"]
    assert rec["$type"] == "com.etzhayyim.himawari.cellBatchRecord"
    assert rec["waferBatchId"] == "wafer-2026-0601-A"
    assert rec["cellArchitecture"] == "TOPCon"


def test_record_has_all_lexicon_required_fields():
    rec = _solve({"waferBatchId": "wb-1", "cellArchitecture": "PERC", "metallization": "copper"})["cell_batch_record"]
    for required in ("batchId", "waferBatchId", "cellArchitecture", "gasAbatementCid", "attestingRobots"):
        assert required in rec and rec[required] not in (None, ""), f"missing required lexicon field {required}"
    assert isinstance(rec["attestingRobots"], list) and len(rec["attestingRobots"]) >= 2


def test_batch_completes_at_100pct():
    out = _solve({"waferBatchId": "wb-2", "cellArchitecture": "HJT", "metallization": "copper"})
    assert out["cell_state"]["completionPct"] == 100
    assert out["cell_state"]["phase"].value == "complete"


# ─── G11 witness quorum ───

def test_witness_quorum_is_two_distinct_robots():
    rec = _solve({"waferBatchId": "wb-3", "cellArchitecture": "TOPCon"})["cell_batch_record"]
    robots = rec["attestingRobots"]
    assert len(set(robots)) >= 2, "G11: need ≥2 distinct robot DIDs"
    assert any("otete" in r for r in robots) and any("mimi" in r for r in robots)


# ─── flash IV ───

def test_flash_iv_median_is_integer_milliwp():
    rec = _solve({"waferBatchId": "wb-4", "cellArchitecture": "HJT", "metallization": "copper"})["cell_batch_record"]
    assert isinstance(rec["flashIvMedianMilliwp"], int)
    assert rec["flashIvMedianMilliwp"] > 0


def test_hjt_outperforms_perc_on_median_power():
    hjt = _solve({"waferBatchId": "wb-hjt", "cellArchitecture": "HJT"})["cell_batch_record"]
    perc = _solve({"waferBatchId": "wb-perc", "cellArchitecture": "PERC"})["cell_batch_record"]
    assert hjt["flashIvMedianMilliwp"] > perc["flashIvMedianMilliwp"]


# ─── G3: high-GWP gas abatement ───

def test_g3_default_batch_meets_99pct_floor():
    out = _solve({"waferBatchId": "wb-5", "cellArchitecture": "TOPCon", "metallization": "copper"})
    abate = out["cell_state"]["gasAbatement"]
    assert abate["allMeetG3"] is True
    assert abate["uncontrolledVenting"] is False
    for line in abate["gases"]:
        assert line["meetsG3Floor"] is True
        assert line["destructionRemovalEfficiency"] >= 0.99 or line["substituted"]


def test_g3_below_floor_halts_no_record():
    """Force a sub-floor abatement DRE → batch must halt, emit no cellBatchRecord."""
    c = cell_mod.CellProcessCell()
    orig = c._gas_abatement

    def patched(state):
        out = orig(state)
        cs = out["cell_state"]
        # Stamp a sub-floor, non-substituted gas to trip the G3 gate.
        cs["gasAbatement"]["gases"] = [
            {"gas": "SF6", "gwp100": 23500, "substituted": False,
             "substituteWith": None, "destructionRemovalEfficiency": 0.80, "meetsG3Floor": False}
        ]
        cs["gasAbatement"]["allMeetG3"] = False
        cs["phase"] = cell_mod.CellPhase.ANOMALY_HALT
        cs["anomalyFlags"] = ["G3:gas-abatement-below-99pct:SF6"]
        cs["errorMsg"] = "G3 violation (test-forced)"
        return {"cell_state": cs, "next_node": "halt"}

    c._gas_abatement = patched  # type: ignore[method-assign]
    out = c.solve({"waferBatchId": "wb-bad", "cellArchitecture": "PERC"})
    assert "cell_batch_record" not in out, "G3 violation must NOT emit a release record"
    assert "alert_record" in out
    assert out["alert_record"]["reason"] == "g3_gas_abatement_anomaly"
    assert out["cell_state"]["phase"].value == "anomaly_halt"


def test_gas_abatement_cid_is_stable():
    a = _solve({"waferBatchId": "wb-c", "cellArchitecture": "TOPCon", "metallization": "copper"})["cell_batch_record"]
    b = _solve({"waferBatchId": "wb-c", "cellArchitecture": "TOPCon", "metallization": "copper"})["cell_batch_record"]
    assert a["gasAbatementCid"] == b["gasAbatementCid"], "abatement CID must be deterministic/replayable"


# ─── G6: Ag→Cu metallization roadmap ───

def test_g6_silver_only_is_flagged_off_roadmap():
    out = _solve({"waferBatchId": "wb-6", "cellArchitecture": "PERC", "metallization": "silver"})
    flags = out["metallizationFlags"]
    assert any("G6" in f and "off-roadmap" in f for f in flags), "silver-only must be flagged against Ag→Cu roadmap"
    # silver-only still produces a record (permitted at R1, just flagged).
    assert "cell_batch_record" in out


def test_g6_copper_is_on_roadmap_no_flag():
    out = _solve({"waferBatchId": "wb-7", "cellArchitecture": "TOPCon", "metallization": "copper"})
    assert out["metallizationFlags"] == [], "copper metallization is on-roadmap, no G6 flag expected"


def test_g6_hybrid_is_on_roadmap_no_flag():
    out = _solve({"waferBatchId": "wb-8", "cellArchitecture": "HJT", "metallization": "ag-cu-hybrid"})
    assert out["metallizationFlags"] == []


# ─── defaults / input hardening ───

def test_unknown_architecture_falls_back_to_topcon():
    rec = _solve({"waferBatchId": "wb-9", "cellArchitecture": "BOGUS"})["cell_batch_record"]
    assert rec["cellArchitecture"] == "TOPCon"


def test_batch_id_derives_from_wafer_batch_when_absent():
    rec = _solve({"waferBatchId": "wb-10"})["cell_batch_record"]
    assert rec["batchId"] == "cell-wb-10"


# ─── lexicon conformance ───

_LEXICON_PATH = (
    pathlib.Path(__file__).resolve().parents[4]
    / "00-contracts/lexicons/com/etzhayyim/himawari/cellBatchRecord.json"
)

# JSON-Schema/atproto primitive type → accepted Python type(s) for the value.
_TYPE_MAP = {
    "string": str,
    "integer": int,
    "boolean": bool,
    "array": list,
    "object": dict,
}


def _load_lexicon():
    return json.loads(_LEXICON_PATH.read_text(encoding="utf-8"))


def _check_obj_against_def(value, def_props, def_required, defs, ctx):
    """Assert `value` (a dict) has every required prop with the right shape."""
    assert isinstance(value, dict), f"{ctx}: expected object, got {type(value).__name__}"
    for prop in def_required:
        assert prop in value, f"{ctx}: missing required lexicon field {prop!r}"
        spec = def_props[prop]
        _check_value_against_spec(value[prop], spec, defs, f"{ctx}.{prop}")


def _check_value_against_spec(value, spec, defs, ctx):
    """Assert a single value matches its lexicon property spec (recursively)."""
    ptype = spec.get("type")
    if ptype == "ref":
        ref = spec["ref"].lstrip("#")
        rdef = defs[ref]
        _check_obj_against_def(value, rdef["properties"], rdef.get("required", []), defs, ctx)
        return
    if ptype == "array":
        assert isinstance(value, list), f"{ctx}: expected array, got {type(value).__name__}"
        if "minItems" in spec:
            assert len(value) >= spec["minItems"], (
                f"{ctx}: array has {len(value)} items, lexicon requires minItems {spec['minItems']}"
            )
        items = spec.get("items", {})
        for i, elem in enumerate(value):
            _check_value_against_spec(elem, items, defs, f"{ctx}[{i}]")
        return
    expected = _TYPE_MAP.get(ptype)
    assert expected is not None, f"{ctx}: unhandled lexicon type {ptype!r}"
    # bool is a subclass of int — guard so an integer field can't pass as bool.
    if expected is int:
        assert isinstance(value, int) and not isinstance(value, bool), (
            f"{ctx}: expected integer, got {type(value).__name__}"
        )
    else:
        assert isinstance(value, expected), (
            f"{ctx}: expected {ptype}, got {type(value).__name__}"
        )


def test_emitted_record_conforms_to_cell_batch_record_lexicon():
    """Every lexicon-required field is present with the correct type/shape.

    Loads the canonical com.etzhayyim.himawari.cellBatchRecord lexicon and
    checks the emitted record against the `main` record `required` list and the
    #robotSignature / #gasAbatement #def types (where the cell emits them).
    """
    lex = _load_lexicon()
    defs = lex["defs"]
    main = defs["main"]["record"]
    required = main["required"]
    props = main["properties"]

    rec = _solve(
        {
            "waferBatchId": "wb-conformance",
            "cellArchitecture": "TOPCon",
            "metallization": "ag-cu-hybrid",
            "recordedAt": "2026-06-02T12:00:00Z",
        }
    )["cell_batch_record"]

    # 1) every top-level required field present with the right type/shape.
    _check_obj_against_def(rec, props, required, defs, "cellBatchRecord")

    # 2) attestingRobots stays a list of DID strings (NOT object-ified — the
    #    lexicon types it as array<string,format:did>).
    assert all(isinstance(r, str) for r in rec["attestingRobots"]), (
        "attestingRobots must remain DID strings per the cellBatchRecord lexicon"
    )

    # 3) recordedAt is emitted and threaded through from input.
    assert rec["recordedAt"] == "2026-06-02T12:00:00Z", "recordedAt must pass through from input"

    # 4) when the cell emits the full #robotSignature bundle, each element must
    #    satisfy the #robotSignature def (robotDid + signature required).
    if "robotSignatures" in rec:
        _check_value_against_spec(
            rec["robotSignatures"], props["robotSignatures"], defs, "cellBatchRecord.robotSignatures"
        )


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"  ok   {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL {fn.__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  ERR  {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
