#!/usr/bin/env python3
"""outbound_logistics — edge-branch coverage (ADR-2606021200 / R1 maturation).

Covers the attestingRobots normalization + the kami-autodrive VehicleClass
parser fallbacks left uncovered by test_outbound_logistics.py:

  - _robot_signatures: bare DID string → minimal #robotSignature;
                       empty input → minItems-1 gnc-dispatch placeholder
  - _load_kami_autodrive_vehicle_classes: source file unreadable (OSError) and
    source present but enum not found → both fall back to the lexicon class set
    (the composition reads sarutahiko/kami-autodrive's Rust enum, and must never
    crash himawari when that sibling source is absent or restructured).
"""
import importlib.util
import pathlib
import tempfile

_spec = importlib.util.spec_from_file_location(
    "himawari_outbound_logistics_cell_e", pathlib.Path(__file__).parent / "cell.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)


def test_robot_signature_bare_did_promoted():
    sigs = _mod.OutboundLogisticsCell._robot_signatures(["did:robot:gnc"])
    assert len(sigs) == 1
    assert sigs[0]["robotDid"] == "did:robot:gnc"
    assert sigs[0]["role"] == "gnc-handoff"
    assert sigs[0]["signature"] == ""  # sealed off-cell, never fabricated


def test_robot_signature_empty_yields_placeholder():
    sigs = _mod.OutboundLogisticsCell._robot_signatures([])
    assert len(sigs) == 1, "minItems 1 — never an empty witness array"
    assert sigs[0]["robotDid"].endswith(":gnc-dispatch")


def test_vehicle_class_parser_falls_back_on_missing_source():
    orig = _mod._KAMI_AUTODRIVE_CLASSES_RS
    _mod._KAMI_AUTODRIVE_CLASSES_RS = pathlib.Path("/nonexistent/kami/autodrive.rs")
    try:
        classes = _mod._load_kami_autodrive_vehicle_classes()
        assert classes == _mod._LEXICON_VEHICLE_CLASSES
    finally:
        _mod._KAMI_AUTODRIVE_CLASSES_RS = orig


def test_vehicle_class_parser_falls_back_when_enum_absent():
    orig = _mod._KAMI_AUTODRIVE_CLASSES_RS
    with tempfile.NamedTemporaryFile("w", suffix=".rs", delete=False) as fh:
        fh.write("// a rust file with no VehicleClass enum at all\npub fn unrelated() {}\n")
        tmp = fh.name
    _mod._KAMI_AUTODRIVE_CLASSES_RS = pathlib.Path(tmp)
    try:
        classes = _mod._load_kami_autodrive_vehicle_classes()
        assert classes == _mod._LEXICON_VEHICLE_CLASSES
    finally:
        _mod._KAMI_AUTODRIVE_CLASSES_RS = orig
        pathlib.Path(tmp).unlink(missing_ok=True)


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
