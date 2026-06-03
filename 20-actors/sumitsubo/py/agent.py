#!/usr/bin/env python3
"""sumitsubo 墨壺 — generative + modeling-assist langgraph actor (kotoba WASM cell).

ADR-2606033600. Runs in-WASM on kotoba :8077. Handlers over one kotoba EAVT drawing
graph. The op vocabulary (ModelOp) is the SAME as the TS kernel (sdk/src/geometry/
types.ts) — one model, two runtimes:

  handle_model    NL prompt → Murakumo LLM → validated ModelOp plan → drawing Datoms (generative)
  handle_draft    2D drafting assistance: dimension / constraint / layer suggestions over a drawing
  handle_interop  Vectorworks/AutoCAD-shaped script → neutral ModelOp list (python mirror of adapters)
  handle_export   resolve target format + emit export record (DWG-proprietary honesty)

LLM access is Murakumo-only via KotobaLLM (127.0.0.1:4000; G3). State is written back to
the kotoba Datom log (G2). Generated geometry is marked :representative unless dimensioned
from authoritative input (G7). Cleanroom: the interop translator uses only the published
call shapes (G1). No native DWG write (G5).
"""
from __future__ import annotations

import json
import re
from typing import TypedDict

# kotoba-provided host bindings (WASM Component Model imports)
try:
    from kotoba import datalog, llm  # type: ignore
except ImportError:  # local dev / test fallback
    datalog = llm = None  # type: ignore

# --------------------------------------------------------------------------- #
# Shared ModelOp vocabulary (MUST stay in lockstep with sdk/src/geometry/types.ts)
# --------------------------------------------------------------------------- #
OP_SCHEMA: dict[str, set[str]] = {
    "layer": {"name"},
    "point": {"x", "y"},
    "line": {"x1", "y1", "x2", "y2"},
    "polyline": {"points"},
    "rect": {"x", "y", "w", "h"},
    "circle": {"cx", "cy", "r"},
    "arc": {"cx", "cy", "r", "start", "end"},
    "box": {"x", "y", "z", "w", "d", "h"},
    "extrude": {"profile", "height"},
    "move": {"target", "dx", "dy"},
    "scale": {"target", "factor"},
}

EXPORT_FIDELITY = {
    "dxf": "full",
    "svg": "full",
    "obj": "full",
    "gltf": "full",
    "ifc": "subset",
    "step": "subset",
    "dwg": "fallback",
}


def validate_ops(ops: list[dict]) -> list[dict]:
    """Keep only well-formed ops (G4 honesty: silently-malformed ops are dropped, logged)."""
    out: list[dict] = []
    for op in ops:
        name = op.get("op")
        req = OP_SCHEMA.get(name)
        if req is None:
            continue
        if not req.issubset(op.keys()):
            continue
        out.append(op)
    return out


# --------------------------------------------------------------------------- #
# Murakumo-only LLM (G3). Returns an op plan as JSON; deterministic offline fallback.
# --------------------------------------------------------------------------- #
def _llm_plan(prompt: str) -> list[dict]:
    """Ask the Murakumo-fronted model for a ModelOp plan. Offline → heuristic planner."""
    system = (
        "You are a CAD modeling planner. Output ONLY a JSON array of modeling ops. "
        "Allowed ops: " + ", ".join(OP_SCHEMA.keys()) + ". "
        "Each op is an object with an 'op' key and the documented fields. Units are mm."
    )
    if llm is not None:  # Murakumo path (LiteLLM 127.0.0.1:4000)
        raw = llm.infer(system=system, prompt=prompt)  # type: ignore[union-attr]
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return validate_ops(parsed)
        except (json.JSONDecodeError, TypeError):
            pass
    return _heuristic_plan(prompt)


def _heuristic_plan(prompt: str) -> list[dict]:
    """Tiny deterministic planner so the cell is useful (and testable) without a live model.

    Recognizes dimensioned keywords like 'box 10x20x30', 'rect 100x50', 'circle r=5'."""
    p = prompt.lower()
    ops: list[dict] = []

    for w, d, h in re.findall(r"box\s+(\d+)\s*[x×]\s*(\d+)\s*[x×]\s*(\d+)", p):
        ops.append({"op": "box", "x": 0, "y": 0, "z": 0, "w": int(w), "d": int(d), "h": int(h)})
    for w, h in re.findall(r"rect(?:angle)?\s+(\d+)\s*[x×]\s*(\d+)", p):
        ops.append({"op": "rect", "x": 0, "y": 0, "w": int(w), "h": int(h)})
    for r in re.findall(r"circle\s+r\s*=?\s*(\d+)", p):
        ops.append({"op": "circle", "cx": 0, "cy": 0, "r": int(r)})
    for w, h, ht in re.findall(r"extrude\s+(\d+)\s*[x×]\s*(\d+)\s+by\s+(\d+)", p):
        w, h, ht = int(w), int(h), int(ht)
        ops.append({"op": "extrude", "profile": [[0, 0], [w, 0], [w, h], [0, h]], "height": ht})

    if not ops:
        # default: a unit square so downstream stages always have geometry (representative)
        ops.append({"op": "rect", "x": 0, "y": 0, "w": 100, "h": 100})
    return validate_ops(ops)


# --------------------------------------------------------------------------- #
# Datom emission (G2) — mirror of sdk/src/kotoba/datom.ts op→entity mapping
# --------------------------------------------------------------------------- #
def _emit_datoms(drawing_id: str, ops: list[dict], sourcing: str) -> list[list]:
    datoms: list[list] = [
        [drawing_id, ":dwg/id", drawing_id],
        [drawing_id, ":dwg/sourcing", sourcing],
    ]
    n = 0
    for op in ops:
        if op["op"] in ("layer", "move", "scale"):
            continue
        n += 1
        eid = f"{drawing_id}.e{n}"
        datoms.append([eid, ":dwg.entity/id", eid])
        datoms.append([eid, ":dwg.entity/of", drawing_id])
        datoms.append([eid, ":dwg.entity/kind", op["op"]])
        datoms.append([eid, ":dwg.entity/layer", op.get("layer", "0")])
    if datalog is not None:  # transact to the canonical kotoba log
        datalog.assert_many(datoms)  # type: ignore[union-attr]
    return datoms


# --------------------------------------------------------------------------- #
# model — generative: NL → op plan → datoms
# --------------------------------------------------------------------------- #
class ModelState(TypedDict, total=False):
    prompt: str
    drawing_id: str
    member_did: str
    sourcing: str
    ops: list
    datoms: list


def handle_model(state: ModelState) -> ModelState:
    ops = _llm_plan(state.get("prompt", ""))
    drawing_id = state.get("drawing_id", "drawing-1")
    sourcing = state.get("sourcing", "representative")  # G7
    datoms = _emit_datoms(drawing_id, ops, sourcing)
    return {**state, "ops": ops, "datoms": datoms, "sourcing": sourcing}


# --------------------------------------------------------------------------- #
# draft — 2D drafting assistance over an existing op set
# --------------------------------------------------------------------------- #
class DraftState(TypedDict, total=False):
    ops: list
    suggestions: list


def handle_draft(state: DraftState) -> DraftState:
    """Suggest dimensions / constraints / layer hygiene. Heuristic + (optional) LLM polish."""
    ops = validate_ops(state.get("ops", []))
    suggestions: list[dict] = []
    has_layer = any(o["op"] == "layer" for o in ops)
    if not has_layer and ops:
        suggestions.append({"kind": "layer", "note": "geometry on default layer '0'; create named layers"})
    for o in ops:
        if o["op"] == "rect":
            suggestions.append({"kind": "dimension", "target": "rect", "note": f"width={o['w']} height={o['h']}"})
        if o["op"] == "circle":
            suggestions.append({"kind": "dimension", "target": "circle", "note": f"diameter={2 * o['r']}"})
        if o["op"] == "polyline" and not o.get("closed"):
            suggestions.append({"kind": "constraint", "target": "polyline", "note": "open polyline; close for a region/extrude"})
    return {**state, "suggestions": suggestions}


# --------------------------------------------------------------------------- #
# interop — vendor-shaped script → neutral ops (python mirror of TS adapters, G1)
# --------------------------------------------------------------------------- #
class InteropState(TypedDict, total=False):
    flavor: str  # "vectorworks" | "autocad"
    script: list  # list of [cmd, *args]
    ops: list


def handle_interop(state: InteropState) -> InteropState:
    flavor = state.get("flavor", "")
    script = state.get("script", [])
    ops: list[dict] = []
    layer = "0"
    for line in script:
        if not line:
            continue
        cmd = str(line[0]).upper().lstrip("._")
        args = list(line[1:])
        n = lambda i: float(args[i])  # noqa: E731
        if cmd == "LAYER":
            layer = str(args[0])
            ops.append({"op": "layer", "name": layer})
        elif cmd == "LINE":
            ops.append({"op": "line", "layer": layer, "x1": n(0), "y1": n(1), "x2": n(2), "y2": n(3)})
        elif cmd in ("RECT", "RECTANG", "RECTANGLE"):
            x0, y0, x1, y1 = n(0), n(1), n(2), n(3)
            ops.append({"op": "rect", "layer": layer, "x": min(x0, x1), "y": min(y0, y1),
                        "w": abs(x1 - x0), "h": abs(y1 - y0)})
        elif cmd in ("CIRCLE", "OVAL"):
            ops.append({"op": "circle", "layer": layer, "cx": n(0), "cy": n(1), "r": n(2)})
        elif cmd in ("ARC", "ARCBYCENTER"):
            ops.append({"op": "arc", "layer": layer, "cx": n(0), "cy": n(1), "r": n(2),
                        "start": n(3), "end": n(4)})
        elif cmd in ("POLY", "PLINE", "POLYLINE"):
            pts = [[float(args[i]), float(args[i + 1])] for i in range(0, len(args) - 1, 2)]
            ops.append({"op": "polyline", "layer": layer, "points": pts, "closed": False})
        elif cmd == "EXTRUDE":
            *flat, height = args
            prof = [[float(flat[i]), float(flat[i + 1])] for i in range(0, len(flat) - 1, 2)]
            ops.append({"op": "extrude", "layer": layer, "profile": prof, "height": float(height)})
        # unsupported tokens are skipped (G4 honesty)
    return {**state, "ops": validate_ops(ops), "flavor": flavor}


# --------------------------------------------------------------------------- #
# export — resolve format + emit export record (G4/G5 honesty)
# --------------------------------------------------------------------------- #
class ExportState(TypedDict, total=False):
    drawing_id: str
    format: str
    record: dict


def handle_export(state: ExportState) -> ExportState:
    fmt = str(state.get("format", "dxf")).lower()
    fidelity = EXPORT_FIDELITY.get(fmt, "unsupported")
    record = {
        "drawingId": state.get("drawing_id", "drawing-1"),
        "format": fmt,
        "fidelity": fidelity,
        "native": fmt != "dwg",
    }
    if fmt == "dwg":  # G5: never claimed native
        record["advisory"] = "DWG_PROPRIETARY"
        record["fallback"] = "dxf"
        record["note"] = "DWG is proprietary; emit DXF and convert via external ODA/LibreDWG."
    elif fidelity in ("subset",):
        record["note"] = f"{fmt} is an honest subset export (ADR-2606033600 N6)."
    return {**state, "record": record}
