#!/usr/bin/env python3
"""polysilicon_refine — cell logic tests (ADR-2606021200).

Pure-logic tests over PolysiliconRefineCell.solve(); no kotoba host bindings
required (the `datalog` import degrades to None in local dev, so writes are
no-ops and the compute path is fully exercised). Verifies the constitutional
invariants that make this cell the structural fix for hikari §G2:

  - G2/N6 XUAR + forced-labor origin → REFUSED, no waiver (constitutional)
  - G2 conflict-mineral In/Ga dopant → refused
  - N1 solar-grade only (logic-grade EG-Si refused)
  - G2 §2(g) incomplete chain-of-custody → refused (missing == fail, no silent pass)
  - G11 ≥2 attesting robots required
  - a clean lot is accepted, anchored (chainOfCustodyCid), routed to ingot_wafer
  - the provenance record matches the lexicon and is built even on refusal (auditable)
"""
import importlib.util
import json
import os
import pathlib
import sys

# Load this sibling cell.py under a UNIQUE module name via importlib. A bare
# `from cell import X` (or even `from himawari.cells...`) collides under
# `pytest cells/` because the six sibling cell.py files share the module name
# `cell`; a unique spec name keeps pytest collection clean across all six.
_CELL_PATH = pathlib.Path(__file__).parent / "cell.py"
_spec = importlib.util.spec_from_file_location("himawari_polysilicon_refine_cell", _CELL_PATH)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
PolysiliconRefineCell = _mod.PolysiliconRefineCell

# Matching lexicon (for the conformance test). It lives at the contracts root,
# reached by ascending from 20-actors/himawari/cells/polysilicon_refine/.
_LEXICON_PATH = (
    pathlib.Path(__file__).resolve().parents[4]
    / "00-contracts/lexicons/com/etzhayyim/himawari/polysiliconProvenanceAttestation.json"
)

# A fully clean, accept-eligible lot.
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


def _solve(overrides):
    state = {**_CLEAN, **overrides}
    return PolysiliconRefineCell().solve(state)


def test_clean_lot_accepted_and_routed():
    out = _solve({})
    assert out["accepted"] is True
    assert out["violations"] == []
    assert out["routeToCell"] == "ingot_wafer"
    assert out["chainOfCustodyCid"].startswith("bafy~sha256-")
    assert out["provenance"]["qaVerdict"] == "accepted"


def test_xuar_origin_refused_no_waiver():
    out = _solve({"declaredOrigin": "Hotan Prefecture, Xinjiang (XUAR)"})
    assert out["accepted"] is False
    assert out["routeToCell"] is None
    assert any("N6 constitutional" in v for v in out["violations"])


def test_xuar_origin_refused_even_with_full_paperwork():
    # full chain-of-custody must NOT rescue an excluded origin (N6 has no waiver)
    out = _solve({"declaredOrigin": "Uyghur autonomous region"})
    assert out["accepted"] is False
    assert any("excluded forced-labor region" in v for v in out["violations"])


def test_conflict_mineral_dopant_refused():
    out = _solve({"dopantElements": ["B", "In"]})
    assert out["accepted"] is False
    assert any("conflict-mineral" in v for v in out["violations"])


def test_logic_grade_refused_n1():
    # logic-grade 9N+ EG-Si belongs to iwakura/fuigo track, not himawari (N1)
    out = _solve({"feedstockGrade": "electronic-grade-9N"})
    assert out["accepted"] is False
    assert any("N1" in v for v in out["violations"])


def test_missing_audit_cid_is_fail_not_silent_pass():
    out = _solve({"sourcingAuditCid": ""})
    assert out["accepted"] is False
    assert any("sourcingAuditCid" in v for v in out["violations"])


def test_missing_origin_attestation_refused():
    out = _solve({"originRegionAttestationCid": ""})
    assert out["accepted"] is False
    assert any("originRegionAttestationCid" in v for v in out["violations"])


def test_requires_two_attesting_robots():
    out = _solve({"attestingRobots": ["kuni-umi:mimi"]})
    assert out["accepted"] is False
    assert any("attestingRobots requires" in v for v in out["violations"])


def test_provenance_record_matches_lexicon_shape():
    out = _solve({})
    prov = out["provenance"]
    assert prov["$type"] == "com.etzhayyim.himawari.polysiliconProvenanceAttestation"
    for required in (
        "lotId", "recordedAt", "feedstockGrade", "originRegionAttestationCid",
        "supplierDid", "sourcingAuditCid", "chainOfCustody", "attestingEngineerDid",
        "attestingRobots",
    ):
        assert required in prov, f"lexicon-required field {required} missing"
    assert len(prov["attestingRobots"]) >= 2


def test_recorded_at_passthrough_deterministic():
    # recordedAt is threaded through from input (no wall-clock) → deterministic.
    out = _solve({"recordedAt": "2026-01-02T03:04:05Z"})
    assert out["provenance"]["recordedAt"] == "2026-01-02T03:04:05Z"


def test_missing_recorded_at_refused():
    out = _solve({"recordedAt": ""})
    assert out["accepted"] is False
    assert any("recordedAt" in v for v in out["violations"])


def test_attesting_robots_are_robot_signature_objects():
    # attestingRobots must be #robotSignature objects (did + signature), NOT strings.
    out = _solve({})
    robots = out["provenance"]["attestingRobots"]
    assert len(robots) >= 2
    for sig in robots:
        assert isinstance(sig, dict), "each attestingRobots entry must be an object"
        assert sig.get("robotDid"), "#robotSignature requires robotDid"
        assert sig.get("signature"), "#robotSignature requires signature"


def test_attesting_robots_passthrough_rich_objects():
    rich = [
        {"robotDid": "did:web:mimi", "signature": "ed25519:real-sig-a", "role": "metrology"},
        {"robotDid": "did:web:otete", "signature": "ed25519:real-sig-b", "role": "handler"},
    ]
    out = _solve({"attestingRobots": rich})
    robots = out["provenance"]["attestingRobots"]
    assert robots[0]["signature"] == "ed25519:real-sig-a"
    assert robots[1]["role"] == "handler"


def test_chain_of_custody_is_array_of_hops_not_scalar():
    # chainOfCustody must be an array of #custodyHop objects (minItems 1),
    # NOT a flat scalar *Cid string.
    out = _solve({})
    coc = out["provenance"]["chainOfCustody"]
    assert isinstance(coc, list), "chainOfCustody must be an array"
    assert len(coc) >= 1, "chainOfCustody minItems 1"
    for hop in coc:
        assert isinstance(hop, dict), "each custodyHop must be an object"
        for req in ("stage", "custodianDid", "regionCode", "evidenceCid"):
            assert hop.get(req) is not None and hop.get(req) != "" or req == "evidenceCid", (
                f"#custodyHop requires {req}"
            )
    # the chain terminates at himawari's own polysilicon-refine custody
    assert any(h.get("stage") == "polysilicon-refine" for h in coc)


def test_chain_of_custody_passthrough_rich_hops():
    rich = [
        {"stage": "quartz-mining", "custodianDid": "did:web:quarry",
         "regionCode": "NO", "evidenceCid": "bafy-quarry"},
        {"stage": "metallurgical-grade-si", "custodianDid": "did:web:mgsi",
         "regionCode": "NO", "evidenceCid": "bafy-mgsi"},
    ]
    out = _solve({"chainOfCustody": rich})
    coc = out["provenance"]["chainOfCustody"]
    assert coc[0]["stage"] == "quartz-mining"
    assert coc[1]["evidenceCid"] == "bafy-mgsi"


def _lexicon_type_ok(value, type_name: str) -> bool:
    if type_name == "string":
        return isinstance(value, str)
    if type_name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if type_name == "array":
        return isinstance(value, list)
    return True


def test_emitted_record_conforms_to_lexicon_required_fields():
    """Every lexicon-required field is emitted with the correct type/shape.

    Loads the matching lexicon json and asserts: (1) each main `required` field is
    present on the emitted record with the right top-level type; (2) the
    chainOfCustody array's items satisfy #custodyHop `required`; (3) the
    attestingRobots array's items satisfy #robotSignature `required`.
    """
    lex = json.loads(_LEXICON_PATH.read_text(encoding="utf-8"))
    main_props = lex["defs"]["main"]["record"]["properties"]
    required = lex["defs"]["main"]["record"]["required"]

    prov = _solve({})["provenance"]

    # (1) every required main field present with correct top-level type
    for field in required:
        assert field in prov, f"lexicon-required field {field!r} not emitted"
        type_name = main_props[field]["type"]
        assert _lexicon_type_ok(prov[field], type_name), (
            f"field {field!r} must be lexicon type {type_name!r}, got {type(prov[field])}"
        )

    # array minItems where the lexicon declares them
    assert len(prov["chainOfCustody"]) >= main_props["chainOfCustody"].get("minItems", 1)
    assert len(prov["attestingRobots"]) >= main_props["attestingRobots"].get("minItems", 1)

    # (2) chainOfCustody items conform to #custodyHop required
    hop_required = lex["defs"]["custodyHop"]["required"]
    hop_props = lex["defs"]["custodyHop"]["properties"]
    for hop in prov["chainOfCustody"]:
        assert isinstance(hop, dict), "#custodyHop must be an object, not a scalar CID"
        for field in hop_required:
            assert field in hop, f"#custodyHop required field {field!r} missing"
            assert _lexicon_type_ok(hop[field], hop_props[field]["type"]), (
                f"#custodyHop.{field} wrong type"
            )

    # (3) attestingRobots items conform to #robotSignature required
    sig_required = lex["defs"]["robotSignature"]["required"]
    sig_props = lex["defs"]["robotSignature"]["properties"]
    for sig in prov["attestingRobots"]:
        assert isinstance(sig, dict), "#robotSignature must be an object, not a DID string"
        for field in sig_required:
            assert field in sig, f"#robotSignature required field {field!r} missing"
            assert _lexicon_type_ok(sig[field], sig_props[field]["type"]), (
                f"#robotSignature.{field} wrong type"
            )


def test_refusal_record_still_anchored_for_audit():
    # a turned-away forced-labor lot must still leave an on-chain trail
    out = _solve({"declaredOrigin": "Kashgar"})
    assert out["accepted"] is False
    assert out["provenance"]["qaVerdict"] == "refused"
    assert out["chainOfCustodyCid"].startswith("bafy~sha256-")
    assert out["provenance"]["violations"], "refusal reasons must be recorded on the record"


def test_chain_of_custody_cid_is_deterministic():
    a = _solve({})["chainOfCustodyCid"]
    b = _solve({})["chainOfCustodyCid"]
    assert a == b, "same lot must hash to the same chain-of-custody CID (tamper-evident)"


def test_chain_of_custody_cid_changes_with_content():
    a = _solve({})["chainOfCustodyCid"]
    b = _solve({"lotId": "POLY-2026-000999"})["chainOfCustodyCid"]
    assert a != b, "a different lot must not collide to the same CID"


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
