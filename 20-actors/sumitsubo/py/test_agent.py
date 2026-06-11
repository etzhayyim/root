#!/usr/bin/env python3
"""sumitsubo 墨壺 — agent cell tests. ADR-2606033600.

Stdlib-only; runnable as `python3 test_agent.py` (no live kotoba/Murakumo needed —
the offline heuristic planner + None host bindings exercise the full op pipeline)."""
from __future__ import annotations

import sys

from agent import (
    EXPORT_FIDELITY,
    handle_draft,
    handle_export,
    handle_interop,
    handle_model,
    validate_ops,
)

_failures = 0


def check(cond: bool, msg: str) -> None:
    global _failures
    if not cond:
        _failures += 1
        print(f"  ✗ {msg}")
    else:
        print(f"  ✓ {msg}")


def test_validate_ops() -> None:
    print("validate_ops")
    good = [{"op": "rect", "x": 0, "y": 0, "w": 10, "h": 10}]
    bad_name = [{"op": "frobnicate"}]
    bad_fields = [{"op": "circle", "cx": 0}]  # missing cy/r
    check(validate_ops(good) == good, "well-formed op kept")
    check(validate_ops(bad_name) == [], "unknown op dropped (G1/G4)")
    check(validate_ops(bad_fields) == [], "op missing required fields dropped")


def test_model_generative() -> None:
    print("handle_model (generative)")
    out = handle_model({"prompt": "make a box 10x20x30 and a circle r=5", "drawing_id": "d1"})
    kinds = [o["op"] for o in out["ops"]]
    check("box" in kinds and "circle" in kinds, "NL prompt → box + circle ops")
    check(out["sourcing"] == "representative", "generated geometry representative (G7)")
    attrs = {d[1] for d in out["datoms"]}
    check(":dwg/id" in attrs and ":dwg.entity/kind" in attrs, "emits :dwg.* datoms (G2)")
    check(any(d[1] == ":dwg/sourcing" for d in out["datoms"]), "sourcing stamped on drawing")


def test_model_default() -> None:
    print("handle_model default")
    out = handle_model({"prompt": "something abstract", "drawing_id": "d2"})
    check(len(out["ops"]) >= 1, "always yields at least one op (default square)")


def test_draft() -> None:
    print("handle_draft")
    ops = [
        {"op": "rect", "x": 0, "y": 0, "w": 40, "h": 20},
        {"op": "circle", "cx": 0, "cy": 0, "r": 5},
        {"op": "polyline", "points": [[0, 0], [1, 1]], "closed": False},
    ]
    out = handle_draft({"ops": ops})
    kinds = {s["kind"] for s in out["suggestions"]}
    check("layer" in kinds, "suggests named layers when on default layer")
    check("dimension" in kinds, "suggests dimensions for rect/circle")
    check("constraint" in kinds, "flags open polyline")


def test_interop_vectorworks() -> None:
    print("handle_interop (vectorworks shape)")
    script = [
        ["Layer", "design"],
        ["Rect", 0, 0, 100, 50],
        ["Oval", 0, 0, 20, 20],
        ["Extrude", 0, 0, 10, 0, 10, 10, 0, 10, 5],
    ]
    out = handle_interop({"flavor": "vectorworks", "script": script})
    kinds = [o["op"] for o in out["ops"]]
    check("layer" in kinds and "rect" in kinds, "VS Layer+Rect translated")
    check("extrude" in kinds, "VS Extrude → extrude op")


def test_interop_autocad() -> None:
    print("handle_interop (autocad shape)")
    script = [
        ["LAYER", "0"],
        ["LINE", 0, 0, 10, 0],
        ["CIRCLE", 5, 5, 2],
        ["PLINE", 0, 0, 10, 0, 10, 10],
        ["BOGUS", 1],  # skipped, G4
    ]
    out = handle_interop({"flavor": "autocad", "script": script})
    kinds = [o["op"] for o in out["ops"]]
    check(kinds.count("line") == 1 and "circle" in kinds, "AutoCAD LINE/CIRCLE translated")
    check("polyline" in kinds, "PLINE → polyline")
    check("frobnicate" not in kinds and len(out["ops"]) == 4, "unsupported token skipped honestly (G4)")


def test_export() -> None:
    print("handle_export")
    dxf = handle_export({"drawing_id": "d1", "format": "dxf"})["record"]
    check(dxf["fidelity"] == "full" and dxf["native"], "dxf full + native")
    ifc = handle_export({"drawing_id": "d1", "format": "ifc"})["record"]
    check(ifc["fidelity"] == "subset" and "note" in ifc, "ifc subset honesty (N6)")
    dwg = handle_export({"drawing_id": "d1", "format": "dwg"})["record"]
    check(dwg["native"] is False and dwg["advisory"] == "DWG_PROPRIETARY", "dwg never native (G5)")
    check(EXPORT_FIDELITY["gltf"] == "full", "gltf full")


def main() -> int:
    for t in (
        test_validate_ops,
        test_model_generative,
        test_model_default,
        test_draft,
        test_interop_vectorworks,
        test_interop_autocad,
        test_export,
    ):
        t()
    print()
    if _failures:
        print(f"FAILED: {_failures} check(s)")
        return 1
    print("ALL PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
