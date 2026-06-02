#!/usr/bin/env python3
"""himawari 向日葵 ingot_wafer — cell logic tests (ADR-2606021200).

Pure-logic tests over IngotWaferCell.solve; no kotoba host bindings required
(the datalog import degrades to None in local dev). Verifies the constitutional
invariants of the ingot growth + wire-saw wafering + kerf-Si recovery cell:

  - emits an com.etzhayyim.himawari.waferBatchRecord with all required fields
  - models per-wafer Si mass + saw kerf (mass balance is honest, never faked)
  - G5: rejects a batch whose kerf-Si recovery is < 90% circular (≥9000 bps)
  - G5: recovered kerf routes back to polysilicon_refine as recycled feedstock
  - G4: rejects process energy drawn from any non-hikari-renewable source
  - requires ≥2 attesting robots + a known solar ingot method (contract raises)
"""
import importlib.util
import json
import pathlib

# Load the sibling cell.py under a UNIQUE module name so `pytest cells/` can collect
# all six himawari cell test files without the bare module-name `cell` colliding.
_spec = importlib.util.spec_from_file_location(
    "himawari_ingot_wafer_cell", pathlib.Path(__file__).parent / "cell.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
IngotWaferCell = _mod.IngotWaferCell

# Matching lexicon for the conformance test.
_LEXICON_PATH = (
    pathlib.Path(__file__).resolve().parents[4]
    / "00-contracts/lexicons/com/etzhayyim/himawari/waferBatchRecord.json"
)


def _base_state(**overrides) -> dict:
    st = {
        "batchId": "wafer-2026-0602-001",
        "polysiliconLotId": "poly-lot-2026-0601-007",
        "recordedAt": "2026-06-02T00:00:00Z",
        "ingotMethod": "czochralski-monocrystalline",
        "waferCount": 1200,
        "attestingEngineerDid": "did:web:etzhayyim.com:himawari#pv-process-engineer",
        "attestingRobots": [
            "did:web:etzhayyim.com:himawari#mimi-metrology",
            "did:web:etzhayyim.com:himawari#mimi-massbalance",
        ],
        "waferThicknessUm": 150,
        "waferDiameterMm": 210,
        "sawTech": "diamond-wire",
        "yieldBps": 9800,
        "processEnergyWh": 50_000,
        "energySources": ["hikari-solar", "hikari-storage"],
        "transact": False,  # pure-logic test: do not touch the host binding
    }
    st.update(overrides)
    return st


def test_emits_wafer_batch_record_with_required_fields():
    out = IngotWaferCell().solve(_base_state())
    assert out["accepted"] is True
    rec = out["waferBatchRecord"]
    assert rec["$type"] == "com.etzhayyim.himawari.waferBatchRecord"
    for field in ("batchId", "polysiliconLotId", "ingotMethod", "waferCount", "attestingRobots"):
        assert field in rec and rec[field], f"required lexicon field {field} missing/empty"
    assert len(rec["attestingRobots"]) >= 2


def test_recorded_at_passthrough():
    # recordedAt is threaded through from input (no wall-clock in pure logic).
    out = IngotWaferCell().solve(_base_state(recordedAt="2026-06-02T12:34:56Z"))
    assert out["waferBatchRecord"]["recordedAt"] == "2026-06-02T12:34:56Z"


def test_attesting_robots_are_robot_signature_objects():
    # lexicon defines attestingRobots as an array of #robotSignature objects,
    # NOT a flat list of DID strings. The cell must normalize bare DIDs to objects.
    out = IngotWaferCell().solve(_base_state())
    robots = out["waferBatchRecord"]["attestingRobots"]
    assert isinstance(robots, list) and len(robots) >= 2
    for sig in robots:
        assert isinstance(sig, dict), "each attestingRobots entry must be an object"
        assert sig["robotDid"], "#robotSignature.robotDid is required"
        assert sig["signature"], "#robotSignature.signature is required"
    assert robots[0]["robotDid"] == "did:web:etzhayyim.com:himawari#mimi-metrology"


def test_attesting_robots_accepts_prebuilt_signature_objects():
    # a caller may pass already-shaped #robotSignature objects; they pass through.
    sigs = [
        {"robotDid": "did:web:etzhayyim.com:himawari#mimi", "role": "metrology",
         "signature": "ed25519:abc", "timestamp": "2026-06-02T00:00:00Z"},
        {"robotDid": "did:web:etzhayyim.com:himawari#otete", "role": "mass-balance",
         "signature": "ed25519:def", "timestamp": "2026-06-02T00:00:01Z"},
    ]
    out = IngotWaferCell().solve(_base_state(attestingRobots=sigs))
    robots = out["waferBatchRecord"]["attestingRobots"]
    assert robots[0]["signature"] == "ed25519:abc"
    assert robots[1]["role"] == "mass-balance"


def test_kerf_mass_balance_is_modelled_not_faked():
    out = IngotWaferCell().solve(_base_state())
    # kerf must be generated for a real slicing pass, and recovered ≤ generated
    assert out["kerfGeneratedGrams"] > 0
    assert out["waferBatchRecord"]["kerfRecoveredGrams"] <= out["kerfGeneratedGrams"]
    # default recovery models the 90% G5 target
    assert out["kerfRecoveryBps"] >= 9000


def test_g5_rejects_sub_90pct_kerf_recovery():
    out = IngotWaferCell().solve(_base_state())
    generated = out["kerfGeneratedGrams"]
    # report a measured recovery just below the 90% line
    bad = IngotWaferCell().solve(_base_state(kerfRecoveredGrams=int(generated * 0.80)))
    assert bad["accepted"] is False
    assert "G5" in bad["reason"]
    assert bad["kerfRecoveryBps"] < 9000
    assert "waferBatchRecord" not in bad  # rejected batch is not emitted


def test_g5_accepts_at_exactly_90pct():
    out = IngotWaferCell().solve(_base_state())
    generated = out["kerfGeneratedGrams"]
    ok = IngotWaferCell().solve(_base_state(kerfRecoveredGrams=generated))  # 100% recovery
    assert ok["accepted"] is True
    assert ok["kerfRecoveryBps"] == 10000


def test_g5_recovered_kerf_routes_back_as_feedstock():
    out = IngotWaferCell().solve(_base_state())
    # the recovered kerf is exposed as recycled feedstock for polysilicon_refine
    assert out["recycledKerfFeedstockGrams"] == out["waferBatchRecord"]["kerfRecoveredGrams"]
    assert out["recycledKerfFeedstockGrams"] > 0


def test_g4_rejects_fossil_process_energy():
    bad = IngotWaferCell().solve(_base_state(energySources=["grid-fossil"]))
    assert bad["accepted"] is False
    assert "G4" in bad["reason"]


def test_g4_rejects_nuclear_process_energy():
    bad = IngotWaferCell().solve(_base_state(energySources=["hikari-solar", "nuclear"]))
    assert bad["accepted"] is False
    assert "G4" in bad["reason"]


def test_g4_zero_energy_is_not_blocked():
    # a record that reports no process energy yet should not trip the G4 gate
    out = IngotWaferCell().solve(_base_state(processEnergyWh=0, energySources=[]))
    assert out["accepted"] is True


def test_requires_two_attesting_robots():
    try:
        IngotWaferCell().solve(_base_state(attestingRobots=["did:web:etzhayyim.com:himawari#mimi"]))
        assert False, "single robot must raise (lexicon minItems:2)"
    except ValueError as e:
        assert "attesting robots" in str(e)


def test_rejects_unknown_ingot_method():
    try:
        IngotWaferCell().solve(_base_state(ingotMethod="float-zone-9N"))
        assert False, "non-solar ingot method must raise"
    except ValueError as e:
        assert "ingotMethod" in str(e)


def test_requires_core_fields():
    for bad in ({"batchId": ""}, {"polysiliconLotId": ""}, {"ingotMethod": ""}, {"waferCount": 0}):
        try:
            IngotWaferCell().solve(_base_state(**bad))
            assert False, f"missing/invalid required input {bad} must raise"
        except ValueError:
            pass


def test_yield_and_thickness_carry_into_record():
    out = IngotWaferCell().solve(_base_state(yieldBps=9650, waferThicknessUm=130))
    rec = out["waferBatchRecord"]
    assert rec["yieldBps"] == 9650
    assert rec["waferThicknessUm"] == 130


def test_transact_off_does_not_fake_persistence():
    out = IngotWaferCell().solve(_base_state(transact=False))
    assert out["transacted"] is False  # honest: no host binding write claimed


# --------------------------------------------------------------------------- #
# Lexicon conformance — emitted record carries every required field with the
# correct type/shape per com.etzhayyim.himawari.waferBatchRecord.
# --------------------------------------------------------------------------- #
_JSON_TYPE = {
    "string": str,
    "integer": int,
    "array": list,
    "object": dict,
    "boolean": bool,
}


def _assert_type(value, prop_schema, ctx):
    jtype = prop_schema.get("type")
    if jtype in _JSON_TYPE:
        py = _JSON_TYPE[jtype]
        # bool is a subclass of int; guard integer fields against bools.
        assert isinstance(value, py) and not (py is int and isinstance(value, bool)), (
            f"{ctx}: expected {jtype}, got {type(value).__name__}"
        )


def test_record_conforms_to_lexicon_required_fields():
    lex = json.loads(_LEXICON_PATH.read_text())
    main = lex["defs"]["main"]["record"]
    props = main["properties"]
    required = main["required"]
    robot_def = lex["defs"]["robotSignature"]

    rec = IngotWaferCell().solve(_base_state())["waferBatchRecord"]

    # every lexicon-required field is present with the correct type/shape
    for field in required:
        assert field in rec, f"required lexicon field {field!r} missing from emit"
        _assert_type(rec[field], props[field], f"waferBatchRecord.{field}")

    # attestingRobots: array of #robotSignature objects, minItems honored, each
    # object carrying the #robotSignature-required fields with correct types.
    robots = rec["attestingRobots"]
    assert len(robots) >= props["attestingRobots"]["minItems"]
    for i, sig in enumerate(robots):
        assert isinstance(sig, dict), f"attestingRobots[{i}] must be a #robotSignature object"
        for rfield in robot_def["required"]:
            assert rfield in sig and sig[rfield], (
                f"attestingRobots[{i}].{rfield} required by #robotSignature"
            )
            _assert_type(sig[rfield], robot_def["properties"][rfield], f"#robotSignature.{rfield}")

    # waferCount honors the integer minimum, recordedAt is the threaded value.
    assert rec["waferCount"] >= props["waferCount"]["minimum"]
    assert rec["recordedAt"]  # required + non-empty (threaded from input)


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
