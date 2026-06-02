#!/usr/bin/env python3
"""ModuleAssemblyCell — cell logic tests (ADR-2606021200).

Pure-logic tests over the module_assembly solver; no kotoba host bindings
required (the datalog import degrades to None in local dev, so writes are
computed but not persisted). Verifies the constitutional invariants that make a
himawari module attestable:

  - G11 serial <-> feedstock lot traceability is mandatory (missing link refused)
  - G11 every module carries flash-IV + EL CIDs + a reproducible signature
  - G11 >= 2 co-attesting robots (process + metrology)
  - G11 deterministic flash binning (out-of-tolerance Wp is binned, not silently passed)
  - G12 internal hikari-only destination (external destination refused)
  - identical metrology -> identical CIDs + signature (content-addressing determinism)
  - lexicon conformance: every moduleAttestation.json required field + #def type/shape
"""
import importlib.util
import json
import pathlib

# Load the sibling cell.py under a UNIQUE module name (the bare module name 'cell'
# collides across the 6 sibling cell.py files when collected under `pytest cells/`).
_spec = importlib.util.spec_from_file_location(
    "himawari_module_assembly_cell", pathlib.Path(__file__).parent / "cell.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
ModuleAssemblyCell = _mod.ModuleAssemblyCell

# moduleAttestation lexicon (SSoT for the required-field conformance test).
_LEXICON_PATH = (
    pathlib.Path(__file__).resolve().parents[4]
    / "00-contracts/lexicons/com/etzhayyim/himawari/moduleAttestation.json"
)

_FLASH = {"curve": [[0.0, 9.8], [40.0, 9.6], [44.0, 0.0]], "irradiance": 1000}
_EL = {"w": 1024, "h": 768, "defects": []}


def _good_state(**over):
    base = {
        "moduleSerial": "HMW-2026-000123",
        "cellBatchId": "CELL-B-0042",
        "feedstockLotId": "POLY-LOT-0007",
        "bomCid": "cid:sbom:sha256:deadbeef",
        "ratedWp": 440,
        "measuredWp": 442,
        "recordedAt": "2026-06-02T12:00:00Z",
        "flashIv": _FLASH,
        "elImage": _EL,
        "destinationActorDid": "did:web:etzhayyim.com:hikari",
        "attestingRobots": ["otete", "mimi"],
        "epbtMonths": 14,
        "recyclabilityBps": 9200,
    }
    base.update(over)
    return base


def test_happy_path_emits_attestation():
    out = ModuleAssemblyCell().solve(_good_state())
    rec = out["moduleAttestation"]
    assert out.get("refused") is not True
    assert out["binned"] is False
    assert rec["moduleSerial"] == "HMW-2026-000123"
    assert rec["feedstockLotId"] == "POLY-LOT-0007"
    assert rec["attestingNode"] == "asher"


def test_g11_missing_feedstock_lot_refused():
    out = ModuleAssemblyCell().solve(_good_state(feedstockLotId=""))
    assert out["refused"] is True
    assert "feedstock lot" in out["reason"]
    assert "moduleAttestation" not in out


def test_g11_missing_cell_batch_refused():
    out = ModuleAssemblyCell().solve(_good_state(cellBatchId=""))
    assert out["refused"] is True
    assert "cell batch" in out["reason"]


def test_g11_provenance_chain_complete():
    out = ModuleAssemblyCell().solve(_good_state())
    chain = out["provenance"]
    assert chain["complete"] is True
    assert chain["link"] == "POLY-LOT-0007->CELL-B-0042->HMW-2026-000123"
    assert chain["chainDigest"].startswith("sha256:")


def test_g11_signature_binds_serial_and_lot():
    out = ModuleAssemblyCell().solve(_good_state())
    sig = out["moduleAttestation"]["signature"]
    assert sig["signedDigest"].startswith("sha256:")
    assert sig["serverHeldKey"] is False
    assert sig["signer"] == "asher"


def test_g11_signature_changes_with_lot():
    a = ModuleAssemblyCell().solve(_good_state())["moduleAttestation"]["signature"]
    b = ModuleAssemblyCell().solve(_good_state(feedstockLotId="POLY-LOT-9999"))[
        "moduleAttestation"
    ]["signature"]
    # a signature cannot be replayed onto a module from a different feedstock lot
    assert a["signedDigest"] != b["signedDigest"]
    assert a["binding"] != b["binding"]


def test_content_addressing_is_deterministic():
    a = ModuleAssemblyCell().solve(_good_state())["moduleAttestation"]
    b = ModuleAssemblyCell().solve(_good_state())["moduleAttestation"]
    assert a["flashIvCid"] == b["flashIvCid"]
    assert a["elImageCid"] == b["elImageCid"]
    assert a["signature"]["signedDigest"] == b["signature"]["signedDigest"]


def test_g11_needs_two_attesting_robots():
    out = ModuleAssemblyCell().solve(_good_state(attestingRobots=["otete"]))
    assert out["refused"] is True
    assert "co-attesting robots" in out["reason"]


def test_g12_external_destination_refused():
    out = ModuleAssemblyCell().solve(
        _good_state(destinationActorDid="did:web:example.com:solarmart")
    )
    assert out["refused"] is True
    assert "external destination" in out["reason"]


def test_g12_non_install_internal_actor_refused():
    out = ModuleAssemblyCell().solve(
        _good_state(destinationActorDid="did:web:etzhayyim.com:yakushi")
    )
    assert out["refused"] is True
    assert "install actor" in out["reason"]


def test_g11_flash_out_of_tolerance_is_binned():
    # measured 480Wp vs rated 440Wp -> ~909bps deviation, beyond 500bps tolerance
    out = ModuleAssemblyCell().solve(_good_state(measuredWp=480))
    assert out["binned"] is True
    assert out["moduleAttestation"]["binReason"].startswith("G11: flash power")
    # binned modules still produce a record (traceability preserved), just flagged
    assert "moduleAttestation" in out


def test_g11_flash_within_tolerance_not_binned():
    out = ModuleAssemblyCell().solve(_good_state(measuredWp=438))
    assert out["binned"] is False
    assert "binReason" not in out["moduleAttestation"]


def test_g5_recyclability_below_floor_flagged():
    out = ModuleAssemblyCell().solve(_good_state(recyclabilityBps=8500))
    assert out["moduleAttestation"]["recyclabilityBelowFloor"] is True


def test_kotoba_write_false_in_local_dev():
    # datalog host binding is None in dev: record computed, not persisted (no fallback store)
    out = ModuleAssemblyCell().solve(_good_state())
    assert out["kotobaWritten"] is False


def test_recorded_at_passthrough():
    # recordedAt is threaded through from input (no wall-clock in the pure-logic cell)
    out = ModuleAssemblyCell().solve(_good_state(recordedAt="2026-06-02T09:30:00Z"))
    assert out["moduleAttestation"]["recordedAt"] == "2026-06-02T09:30:00Z"


def test_attesting_robots_are_robot_signature_objects():
    # G11: attestingRobots emit as #robotSignature objects (robotDid + signature),
    # never a flat list of name strings.
    rec = ModuleAssemblyCell().solve(_good_state())["moduleAttestation"]
    robots = rec["attestingRobots"]
    assert isinstance(robots, list) and len(robots) >= 2
    for r in robots:
        assert isinstance(r, dict)
        assert r["robotDid"].startswith("did:")
        assert isinstance(r["signature"], str) and r["signature"]
    # distinct witnesses -> distinct bindings (a witness cannot be replayed)
    assert robots[0]["signature"] != robots[1]["signature"]


def test_attesting_robots_accept_prebuilt_dicts():
    # a caller may supply robotSignature-shaped dicts; required fields are preserved
    out = ModuleAssemblyCell().solve(
        _good_state(
            attestingRobots=[
                {"robotDid": "did:web:etzhayyim.com:himawari:robot:otete",
                 "role": "stringing", "signature": "ed25519:abcd"},
                {"name": "mimi"},
            ]
        )
    )
    robots = out["moduleAttestation"]["attestingRobots"]
    assert robots[0]["signature"] == "ed25519:abcd"
    assert robots[0]["role"] == "stringing"
    assert robots[1]["robotDid"].endswith("robot:mimi")
    assert robots[1]["signature"]  # deterministically filled


def _lexicon_type_ok(value, prop_def, defs):
    """Validate a value against a lexicon property def (scalar / ref / array)."""
    t = prop_def.get("type")
    if t == "string":
        return isinstance(value, str)
    if t == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if t == "boolean":
        return isinstance(value, bool)
    if t == "ref":
        ref_name = prop_def["ref"].lstrip("#")
        return _lexicon_object_ok(value, defs[ref_name], defs)
    if t == "array":
        if not isinstance(value, list):
            return False
        if len(value) < prop_def.get("minItems", 0):
            return False
        return all(_lexicon_type_ok(v, prop_def["items"], defs) for v in value)
    return True


def _lexicon_object_ok(value, def_obj, defs):
    if not isinstance(value, dict):
        return False
    props = def_obj.get("properties", {})
    for req in def_obj.get("required", []):
        assert req in value, f"#def missing required field {req!r}"
        assert _lexicon_type_ok(value[req], props[req], defs), (
            f"#def field {req!r} wrong type/shape"
        )
    return True


def test_lexicon_conformance_every_required_field():
    """The emitted record contains every moduleAttestation.json required field with
    the correct type/shape, including the #moduleSignature + #robotSignature ref defs."""
    lex = json.loads(_LEXICON_PATH.read_text())
    defs = lex["defs"]
    main = defs["main"]["record"]
    props = main["properties"]
    required = main["required"]

    rec = ModuleAssemblyCell().solve(_good_state())["moduleAttestation"]

    for field in required:
        assert field in rec, f"missing lexicon-required field: {field!r}"
        assert _lexicon_type_ok(rec[field], props[field], defs), (
            f"lexicon-required field {field!r} has wrong type/shape"
        )

    # spot-check the two object-array / ref required fields explicitly
    assert isinstance(rec["attestingRobots"], list) and len(rec["attestingRobots"]) >= 2
    for r in rec["attestingRobots"]:
        assert {"robotDid", "signature"} <= set(r)
    assert {"alg", "signedDigest", "signer", "serverHeldKey"} <= set(rec["signature"])


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
