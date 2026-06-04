#!/usr/bin/env python3
"""himawari 向日葵 outbound_logistics (輸送) — cell logic tests.

Pure-logic tests over the OutboundLogisticsCell super-step pipeline; no kotoba
host binding, no langgraph, no pytest required. Run directly:

    python3 test_outbound_logistics.py

Asserts the cell composes kami-autodrive GNC, wires the existing
open-customs-clearance BPMN, enforces G13 (no weaponization / encrypted
telemetry / own-module → hikari only), and emits an outboundManifest record.
Per ADR-2606021200.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import sys

# Load the sibling cell.py under a UNIQUE module name so `pytest cells/` can
# collect this file without the bare module name `cell` colliding across the 6
# sibling cell.py files. The standalone `__main__` runner below still works too.
_spec = importlib.util.spec_from_file_location(
    "himawari_outbound_logistics_cell", pathlib.Path(__file__).parent / "cell.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
OutboundLogisticsCell = _mod.OutboundLogisticsCell

# Path to the matching lexicon (for the conformance test).
_LEXICON_PATH = (
    pathlib.Path(__file__).resolve().parents[4]
    / "00-contracts"
    / "lexicons"
    / "com"
    / "etzhayyim"
    / "himawari"
    / "outboundManifest.json"
)

HIKARI = "did:web:etzhayyim.com:hikari:site-001"


def _base_state(**overrides):
    st = {
        "manifestId": "himawari:obm:0001",
        "recordedAt": "2026-06-02T00:00:00Z",
        "loadingRecord": {
            "loadingId": "himawari:load:0001",
            "recordCid": "bafyloading0001",
            "moduleSerials": ["HMW-2606-0001", "HMW-2606-0002"],
        },
        "consigneeDid": HIKARI,
        "carrierClass": "car",
        "transportMode": "road",
        "originSite": "did:web:etzhayyim.com:himawari",
        "attestingRobots": [
            {
                "robotDid": "did:web:etzhayyim.com:sarutahiko:f10-loader-01",
                "signature": "ed25519:deadbeef",
                "role": "loader-dispatch",
                "timestamp": "2026-06-02T00:00:00Z",
            }
        ],
    }
    st.update(overrides)
    return st


def test_happy_path_emits_outbound_manifest():
    out = OutboundLogisticsCell().solve(_base_state())
    rec = out["outboundManifest"]
    assert rec["$type"] == "com.etzhayyim.himawari.outboundManifest"
    assert rec["manifestId"] == "himawari:obm:0001"
    assert rec["moduleSerials"] == ["HMW-2606-0001", "HMW-2606-0002"]
    assert out["outbound_state"]["completionPct"] == 100
    assert out["outbound_state"]["phase"] == "complete"


def test_carrier_class_is_a_kami_autodrive_class():
    rec = OutboundLogisticsCell().solve(_base_state())["outboundManifest"]
    assert rec["carrierClass"] in {"car", "ship", "drone", "aircraft"}
    assert rec["routeRequest"]["gnc"] == "kami-autodrive"


def test_marine_mode_defaults_to_ship_class():
    st = _base_state(transportMode="marine")
    del st["carrierClass"]  # let the cell pick
    rec = OutboundLogisticsCell().solve(st)["outboundManifest"]
    assert rec["carrierClass"] == "ship", "marine leg must map to kami-autodrive ship class (funadaiku/funamori)"


def test_unknown_carrier_class_rejected():
    st = _base_state(carrierClass="hovercraft")
    try:
        OutboundLogisticsCell().solve(st)
        raise AssertionError("expected ValueError for non-kami-autodrive class")
    except ValueError as e:
        assert "kami-autodrive" in str(e)


def test_g13_non_hikari_consignee_rejected():
    # G13 / N10: own-module → hikari install only; no external commercial carriage.
    st = _base_state(consigneeDid="did:web:example.com:retail-buyer")
    try:
        OutboundLogisticsCell().solve(st)
        raise AssertionError("expected G13 ValueError for non-hikari consignee")
    except ValueError as e:
        assert "G13" in str(e)


def test_g13_telemetry_encrypted_and_no_weaponization():
    rec = OutboundLogisticsCell().solve(_base_state())["outboundManifest"]
    assert rec["telemetryEncrypted"] is True
    assert rec["weaponizationPayload"] is False
    assert rec["routeRequest"]["telemetryChannel"].startswith("com.etzhayyim.encrypted")
    assert rec["destinationKind"] == "hikari-install-site"


def test_cross_border_wires_existing_customs_bpmn():
    st = _base_state(
        crossBorder=True,
        hsCode="854143",
        declaredValueUsd=125000.0,
        lodgedAt="2026-06-02T00:00:00Z",
    )
    rec = OutboundLogisticsCell().solve(st)["outboundManifest"]
    customs = rec["customs"]
    # MUST reuse the REAL existing engine namespace, not the non-existent
    # com.etzhayyim.apps.customsClearance.* path nor a parallel fork.
    assert customs["engine"] == "com.etzhayyim.etzhayyim.apps.customsClearance"
    assert "open-customs-clearance" in customs["bpmn"]
    decl = customs["lodgeDeclaration"]
    # conforms to the real lodgeDeclaration lexicon required fields.
    assert decl["declarationId"] == "himawari:obm:0001:decl"
    assert decl["hsCode"] == "854143"
    assert decl["declaredValueUsd"] == 125000  # coerced to integer per #lodgeDeclaration
    assert decl["lodgedAt"] == "2026-06-02T00:00:00Z"
    assert decl["manifestVid"] == "himawari:obm:0001"
    assert customs["releaseShipmentRef"] == "himawari:obm:0001:release"


def test_domestic_leg_skips_customs_explicitly():
    rec = OutboundLogisticsCell().solve(_base_state())["outboundManifest"]
    assert rec["customs"]["required"] is False


def test_route_request_carries_origin_and_destination():
    rec = OutboundLogisticsCell().solve(_base_state())["outboundManifest"]
    route = rec["routeRequest"]
    assert route["origin"] == "did:web:etzhayyim.com:himawari"
    assert route["destination"] == HIKARI


def _lexicon():
    return json.loads(_LEXICON_PATH.read_text(encoding="utf-8"))


_LEX_TYPE_TO_PY = {
    "string": str,
    "boolean": bool,
    "integer": int,
    "number": (int, float),
    "array": list,
    "object": dict,
}


def _assert_field_type(name, value, prop_schema, defs):
    """Assert `value` matches the lexicon property schema's type/shape."""
    ptype = prop_schema.get("type")
    if ptype == "ref":
        ref = prop_schema["ref"].lstrip("#")
        sub = defs[ref]
        assert isinstance(value, dict), f"{name}: expected object for ref #{ref}"
        for req in sub.get("required", []):
            assert req in value, f"{name}.#{ref}: missing required sub-field {req!r}"
        return
    if ptype == "array":
        assert isinstance(value, list), f"{name}: expected array, got {type(value)}"
        if "minItems" in prop_schema:
            assert len(value) >= prop_schema["minItems"], (
                f"{name}: array has {len(value)} items < minItems {prop_schema['minItems']}"
            )
        item = prop_schema.get("items", {})
        for i, el in enumerate(value):
            if item.get("type") == "ref":
                ref = item["ref"].lstrip("#")
                sub = defs[ref]
                assert isinstance(el, dict), f"{name}[{i}]: expected #{ref} object"
                for req in sub.get("required", []):
                    assert req in el, f"{name}[{i}].#{ref}: missing required {req!r}"
            elif item.get("type") in _LEX_TYPE_TO_PY:
                assert isinstance(el, _LEX_TYPE_TO_PY[item["type"]]), (
                    f"{name}[{i}]: expected {item['type']}"
                )
        return
    py = _LEX_TYPE_TO_PY.get(ptype)
    if py is not None:
        # bool is a subclass of int; guard so a boolean field is not accepted as integer.
        if ptype == "integer":
            assert isinstance(value, int) and not isinstance(value, bool), (
                f"{name}: expected integer, got {type(value)}"
            )
        else:
            assert isinstance(value, py), f"{name}: expected {ptype}, got {type(value)}"
    if "const" in prop_schema:
        assert value == prop_schema["const"], (
            f"{name}: expected const {prop_schema['const']!r}, got {value!r}"
        )


def test_emitted_record_conforms_to_lexicon_required_fields():
    """Assert the emitted record contains EVERY lexicon-required field with the
    correct type/shape (loads outboundManifest.json; checks #main.required + each
    field's #def type, including the #routeRequest + #robotSignature refs)."""
    lex = _lexicon()
    main = lex["defs"]["main"]["record"]
    props = main["properties"]
    required = main["required"]

    rec = OutboundLogisticsCell().solve(_base_state())["outboundManifest"]

    # 1) every required top-level field is present...
    for field in required:
        assert field in rec, f"emitted record missing lexicon-required field {field!r}"
        # ...and has the lexicon-declared type/shape.
        _assert_field_type(field, rec[field], props[field], lex["defs"])

    # 2) the #robotSignature array elements are objects (NOT flat DID strings).
    assert isinstance(rec["attestingRobots"], list)
    assert len(rec["attestingRobots"]) >= 1
    for sig in rec["attestingRobots"]:
        assert isinstance(sig, dict), "attestingRobots must be #robotSignature objects"
        assert "robotDid" in sig and "signature" in sig

    # 3) the #routeRequest ref's own required fields are present.
    route_req = lex["defs"]["routeRequest"]["required"]
    for f in route_req:
        assert f in rec["routeRequest"], f"routeRequest missing required {f!r}"

    # 4) carrierClass is a real kami-autodrive VehicleClass (parsed from classes.rs).
    assert rec["carrierClass"] in _mod._load_kami_autodrive_vehicle_classes()


def test_carrier_classes_match_real_kami_autodrive_enum():
    """The parsed VehicleClass set is the real enum, == lexicon knownValues."""
    parsed = _mod._load_kami_autodrive_vehicle_classes()
    assert parsed == {"car", "ship", "drone", "aircraft"}, (
        f"parsed kami-autodrive VehicleClass {sorted(parsed)} drifted from lexicon knownValues"
    )


if __name__ == "__main__":
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
