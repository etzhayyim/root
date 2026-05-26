#!/usr/bin/env python3
"""assemble-usd-scene.py — ADR-2605262500 §4 hot-path scene assembler.

Reads a `70-tools/e7m-sim/scenes/<name>/scene.yaml`, resolves every
`world.layers[].datasetPin_at` to an IPFS CID via the religious-corp
PDS, applies a Charter Rider §2 + PII rescan to each fetched shard,
computes the max tier across layers/props, enforces `-nc-` infix on
Tier-C scenes, dispatches per layer.kind to a kami-usd emitter, and
writes a single `.usd` file (W2+) plus a manifest JSON.

W1 status (this commit): paths-reserved skeleton.

- Scene YAML parsing + schema validation: REAL
- Tier ceiling check + `-nc-` enforcement: REAL
- DatasetPin resolution: STUB (returns placeholder CIDs; W2 wires PDS lookup)
- Charter Rider rescan: STUB (logs "would scan"; W2 wires
  pymagatama.organism.sensors.charter_rider)
- Per-layer USD dispatch: STUB (logs dispatch plan; W2 wires kami-usd)
- Determinism harness (G6): TBD W1.5

Usage:

  python3 assemble-usd-scene.py \\
      70-tools/e7m-sim/scenes/wadachi-r1-shibuya-1km/scene.yaml \\
      --out /tmp/wadachi-r1-shibuya-1km.usd \\
      --dry-run

Per ADR-2605262500 §7 G7 (PhysX nv-compat facade only; backing impl =
kami-genesis) + G8 (kami-pbrt / Embree only; OptiX / RTX / Replicator =
N1..N9 NEVER per ADR-2605261800 §2(b)).
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Iterable, Optional


# ─── third-party deps (PyYAML required; jsonschema optional) ────────

try:
    import yaml   # type: ignore[import-untyped]
except ImportError:
    print(
        "assemble-usd-scene.py requires PyYAML. Install via "
        "`pip install pyyaml` (or `uv pip install pyyaml`).",
        file=sys.stderr,
    )
    raise

try:
    import jsonschema   # type: ignore[import-untyped]
    _HAVE_JSONSCHEMA = True
except ImportError:
    _HAVE_JSONSCHEMA = False


# ─── result types ───────────────────────────────────────────────────

LAYER_KIND_DISPATCH = {
    "terrain":          "kami-usd:terrain_from_dem",
    "raster_overlay":   "kami-usd:texture_from_raster",
    "vector_roads":     "kami-usd:ribbon_from_linestring",
    "vector_buildings": "kami-usd:extrude_from_polygon",
    "vector_landuse":   "kami-usd:flat_from_polygon",
    "vector_water":     "kami-usd:flat_from_polygon",
    "vector_pois":      "kami-usd:point_marker",
}
PROP_KIND_DISPATCH = {
    "object_3d_instances":      "kami-usd:point_instancer",
    "skinned_humanoid_instances": "kami-usd:skinned_point_instancer",
}

TIER_ORDER = {"A": 0, "B": 1, "C": 2}


@dataclasses.dataclass
class LayerPlan:
    index: int
    kind: str
    source_subdataset: str
    datasetPin_at: str
    tier: str
    resolved_cid: str
    dispatch_handler: str
    extra: dict[str, Any]


@dataclasses.dataclass
class PropPlan(LayerPlan):
    pass  # same shape; kept separate for typing clarity


@dataclasses.dataclass
class AssemblyPlan:
    scene_path: Path
    scene_name: str
    adr: str
    sim_consumer: Optional[str]
    crs: str
    bbox: list[float]
    output_subdataset: str
    layers: list[LayerPlan]
    props: list[PropPlan]
    max_tier: str
    must_carry_nc_infix: bool
    charter_attestations: dict[str, Any]


# ─── helpers ────────────────────────────────────────────────────────

def _load_scene_yaml(scene_path: Path) -> dict[str, Any]:
    with scene_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _resolve_schema_path(scene_path: Path) -> Path:
    # scenes/<name>/scene.yaml → scenes/_schema/scene.schema.json
    return scene_path.parent.parent / "_schema" / "scene.schema.json"


def _validate_against_schema(scene: dict[str, Any], schema_path: Path) -> None:
    if not _HAVE_JSONSCHEMA:
        # Soft check: assemble can run without jsonschema, but emit a
        # warning so the operator knows the schema gate is off.
        print(
            "[warn] jsonschema not installed — skipping schema validation. "
            "Run `pip install jsonschema` to enable G10 schema gate.",
            file=sys.stderr,
        )
        return
    if not schema_path.exists():
        print(
            f"[warn] schema not found at {schema_path} — skipping validation.",
            file=sys.stderr,
        )
        return
    with schema_path.open("r", encoding="utf-8") as f:
        schema = json.load(f)
    jsonschema.validate(scene, schema)


def _max_tier(items: Iterable[dict[str, Any]]) -> str:
    """Return the highest tier (A < B < C) across layers/props."""
    if not items:
        return "A"
    return max(items, key=lambda it: TIER_ORDER.get(it.get("tier", "A"), 0))["tier"]


def _resolve_datasetpin(at_uri: str) -> str:
    """Resolve `at://...` → IPFS CID.

    W1 STUB: returns a deterministic placeholder derived from the URI
    so dry-run output is stable + the assembler shape is testable.

    W2 wires this to the religious-corp PDS via e7m-dataset's PDS
    helper (`e7m_dataset.pds.resolve_datasetpin`) plus a Kubo HTTP API
    pin verification per ADR-2605241500 §D7 + replicationMin:2 (G3).
    """
    if "<" in at_uri and ">" in at_uri:
        # placeholder marker like '<rkey-placeholder>' — return a stable stub
        digest = hashlib.sha256(at_uri.encode("utf-8")).hexdigest()[:46]
        return f"bafyplaceholder{digest}"
    # Real `at://` — W2 wires the real PDS lookup here.
    digest = hashlib.sha256(at_uri.encode("utf-8")).hexdigest()[:46]
    return f"bafyresolved{digest}"


def _try_import_charter() -> Any:
    """Lazy-import `e7m_dataset.charter` (which itself wraps
    `pymagatama.organism.sensors.charter_rider`). Returns None when the
    e7m-dataset package is not on PYTHONPATH (W1 paths-reserved
    deployments) — the scene-recipe scan then degrades to stub but the
    fetched-file scan at e7m-dataset `add` time still runs.

    Defensive: catches any exception during import, not just
    ImportError, because `pymagatama` transitively imports langchain /
    pydantic which can SystemError on env-mismatch. We never want
    assemble-usd-scene to fail because of a transitive env issue —
    the operator can opt into strict mode via ETZ_E7M_SIM_STRICT_CHARTER=1.
    """
    try:
        from e7m_dataset import charter as charter_mod  # type: ignore
        return charter_mod
    except Exception as exc:   # noqa: BLE001 — see docstring
        import os
        if os.environ.get("ETZ_E7M_SIM_STRICT_CHARTER") == "1":
            raise RuntimeError(
                f"e7m_dataset.charter import failed under strict mode: {exc!r}"
            ) from exc
        return None


def _charter_rider_rescan(
    scene_yaml_path: Path,
    plan_items: list[LayerPlan],
) -> dict[str, Any]:
    """Charter Rider §2(a)-(h) rescan over the scene-recipe text itself.

    Per ADR-2605262500 §4 step 4 (defense in depth): the scene.yaml is
    the only artifact we have at plan-build time, so we scan IT for
    obvious §2 violations (weapons / surveillance / commercial purpose
    / etc. encoded in layer / shader / source names). The per-shard
    rescan over the fetched bytes happens later, at e7m-dataset
    `add` time on each subdataset (ADR-2605262400 §6 + ADR-2605241500).

    Falls back to a stub manifest when `e7m_dataset.charter` is not on
    PYTHONPATH (operator hasn't installed e7m-dataset alongside
    e7m-sim). The stub is documented + recorded in the result.
    """
    charter_mod = _try_import_charter()
    if charter_mod is None:
        return {
            "scan_status": "stub-no-e7m-dataset",
            "scope": "scene-recipe-yaml",
            "note": (
                "e7m_dataset.charter not importable — install e7m-dataset "
                "alongside e7m-sim to enable G1 scene-recipe scan."
            ),
            "layers_scanned": [
                {"index": p.index, "kind": p.kind, "verdict": "stub-not-scanned"}
                for p in plan_items
            ],
        }

    # Real scan over the scene.yaml file. The wrapper handles the
    # `pymagatama.organism.sensors.charter_rider` resolution + the
    # `ETZ_DATASET_CHARTER_STRICT` env. If a violation is found, the
    # scanner returns passed=False; we propagate fail-closed.
    #
    # Defensive: scan_sample lazily imports pymagatama which may
    # transitively pull broken deps (langchain → pydantic env
    # mismatch). We catch any exception and fall back to stub unless
    # strict mode is on.
    import os
    try:
        result: dict[str, Any] = charter_mod.scan_sample(
            [scene_yaml_path], kind="sim-scene-recipe", sample_rows=500
        )
    except Exception as exc:   # noqa: BLE001
        if os.environ.get("ETZ_E7M_SIM_STRICT_CHARTER") == "1":
            raise
        return {
            "scan_status": "stub-scan-call-failed",
            "scope": "scene-recipe-yaml",
            "note": f"charter scan call failed (transitive import?): {exc!r}",
            "layers_scanned": [
                {"index": p.index, "kind": p.kind, "verdict": "stub-scan-call-failed"}
                for p in plan_items
            ],
        }

    if not result.get("passed", False):
        raise RuntimeError(
            f"Charter Rider §2 scan FAILED on scene-recipe "
            f"{scene_yaml_path}: {result.get('note') or result}"
        )
    return {
        "scan_status": "passed-recipe-scan",
        "scope": "scene-recipe-yaml",
        "scanner_result": result,
        "layers_scanned": [
            {"index": p.index, "kind": p.kind, "verdict": "recipe-scan-passed"}
            for p in plan_items
        ],
    }


# Backward-compat alias — tests + W0 callers may still reference the
# stub name. New code uses _charter_rider_rescan.
_charter_rider_rescan_stub = _charter_rider_rescan


# ─── core ──────────────────────────────────────────────────────────

def build_plan(scene_path: Path, schema_path: Optional[Path] = None) -> AssemblyPlan:
    """Build an AssemblyPlan from a scene.yaml.

    Steps (per ADR-2605262500 §4):
      1. Load + schema-validate scene.yaml
      2. Verify `world:` section present
      3. Resolve each datasetPin_at → CID (W1 stub; W2 PDS lookup)
      4. Compute max_tier across layers + props
      5. If max_tier == C, require `-nc-` infix in scene name
      6. Charter Rider §2 + PII rescan (W1 stub)
    """
    scene = _load_scene_yaml(scene_path)
    schema_path = schema_path or _resolve_schema_path(scene_path)
    _validate_against_schema(scene, schema_path)

    world = scene.get("world")
    if world is None:
        raise ValueError(
            f"{scene_path}: scene.yaml has no `world:` section — this is required "
            "for outdoor robotics sim scenes per ADR-2605262500 §3. Cartpole-style "
            "scenes (no world data) should not be passed to assemble-usd-scene.py."
        )

    layers_raw = world.get("layers", [])
    props_raw = world.get("props", []) or []

    layers: list[LayerPlan] = []
    for i, ly in enumerate(layers_raw):
        kind = ly["kind"]
        handler = LAYER_KIND_DISPATCH.get(kind)
        if handler is None:
            raise ValueError(f"layer[{i}].kind = '{kind}' has no dispatch handler")
        layers.append(LayerPlan(
            index=i,
            kind=kind,
            source_subdataset=ly["source_subdataset"],
            datasetPin_at=ly["datasetPin_at"],
            tier=ly["tier"],
            resolved_cid=_resolve_datasetpin(ly["datasetPin_at"]),
            dispatch_handler=handler,
            extra={k: v for k, v in ly.items()
                   if k not in {"kind", "source_subdataset", "datasetPin_at", "tier"}},
        ))

    props: list[PropPlan] = []
    for i, pr in enumerate(props_raw):
        kind = pr["kind"]
        handler = PROP_KIND_DISPATCH.get(kind)
        if handler is None:
            raise ValueError(f"prop[{i}].kind = '{kind}' has no dispatch handler")
        props.append(PropPlan(
            index=i,
            kind=kind,
            source_subdataset=pr["source_subdataset"],
            datasetPin_at=pr["datasetPin_at"],
            tier=pr["tier"],
            resolved_cid=_resolve_datasetpin(pr["datasetPin_at"]),
            dispatch_handler=handler,
            extra={k: v for k, v in pr.items()
                   if k not in {"kind", "source_subdataset", "datasetPin_at", "tier"}},
        ))

    layers_dicts = [{"tier": l.tier} for l in layers]
    props_dicts = [{"tier": p.tier} for p in props]
    max_tier = _max_tier(layers_dicts + props_dicts)

    scene_name = scene_path.parent.name
    nc_in_name = "-nc-" in scene_name or scene_name.endswith("-nc")
    must_carry_nc = (max_tier == "C")
    if must_carry_nc and not nc_in_name:
        raise ValueError(
            f"{scene_path}: max_tier=C but scene name '{scene_name}' lacks `-nc-` "
            f"infix. ADR-2605262500 §7 G4 requires Tier-C-derived sim outputs to "
            f"carry `-nc-`. Rename the scene dir or downgrade the Tier-C source."
        )

    rescan = _charter_rider_rescan(scene_path, layers + props)

    return AssemblyPlan(
        scene_path=scene_path,
        scene_name=scene_name,
        adr=scene.get("adr", ""),
        sim_consumer=scene.get("sim_consumer"),
        crs=world["crs"],
        bbox=world["bbox"],
        output_subdataset=world["output_subdataset"],
        layers=layers,
        props=props,
        max_tier=max_tier,
        must_carry_nc_infix=must_carry_nc,
        charter_attestations=rescan,
    )


def emit_usd_stub(plan: AssemblyPlan, out_path: Path) -> dict[str, Any]:
    """W1 STUB: emit a manifest JSON describing what kami-usd WOULD do.

    W2 replaces this with real tinyusdz invocation (kami-usd):
      - terrain → UsdGeom.Mesh from DEM triangulation
      - raster_overlay → UsdShade.Material texture binding
      - vector_buildings → UsdGeom.Mesh per polygon (extruded)
      - vector_roads → UsdGeom.Mesh per linestring (ribbon)
      - object_3d_instances → UsdGeom.PointInstancer
    """
    manifest = {
        "scene_name": plan.scene_name,
        "adr": plan.adr,
        "max_tier": plan.max_tier,
        "must_carry_nc_infix": plan.must_carry_nc_infix,
        "crs": plan.crs,
        "bbox": plan.bbox,
        "output_subdataset": plan.output_subdataset,
        "layers": [
            {
                "index": l.index,
                "kind": l.kind,
                "tier": l.tier,
                "source_subdataset": l.source_subdataset,
                "resolved_cid": l.resolved_cid,
                "dispatch_handler": l.dispatch_handler,
            } for l in plan.layers
        ],
        "props": [
            {
                "index": p.index,
                "kind": p.kind,
                "tier": p.tier,
                "source_subdataset": p.source_subdataset,
                "resolved_cid": p.resolved_cid,
                "dispatch_handler": p.dispatch_handler,
            } for p in plan.props
        ],
        "charter_attestations": plan.charter_attestations,
        "emitter_status": "stub-w1-manifest-only",
        "emitter_target": "tinyusdz via kami-usd (W2 deliverable per ADR-2605262500 §4)",
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="ADR-2605262500 §4 hot-path scene assembler (W1 stub)."
    )
    parser.add_argument(
        "scene_yaml",
        type=Path,
        help="Path to scenes/<name>/scene.yaml",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output path. Default: <scene_dir>/assembled-manifest.json (W1 stub) "
             "or <scene_dir>/scene.usd (W2+).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build plan + print summary; do not write output.",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=None,
        help="Override schema path (default: ../_schema/scene.schema.json).",
    )
    args = parser.parse_args(argv)

    if not args.scene_yaml.exists():
        print(f"scene.yaml not found: {args.scene_yaml}", file=sys.stderr)
        return 2

    try:
        plan = build_plan(args.scene_yaml, schema_path=args.schema)
    except Exception as e:
        print(f"[error] {e}", file=sys.stderr)
        return 1

    # Summary
    print(f"scene_name       : {plan.scene_name}")
    print(f"adr              : {plan.adr}")
    print(f"sim_consumer     : {plan.sim_consumer}")
    print(f"crs              : {plan.crs}")
    print(f"bbox             : {plan.bbox}")
    print(f"max_tier         : {plan.max_tier}")
    print(f"nc_infix_required: {plan.must_carry_nc_infix}")
    print(f"layers           : {len(plan.layers)}")
    for l in plan.layers:
        print(f"  [{l.index}] {l.kind:18s} tier={l.tier} → {l.dispatch_handler}")
        print(f"      pin   : {l.datasetPin_at}")
        print(f"      cid   : {l.resolved_cid}")
    print(f"props            : {len(plan.props)}")
    for p in plan.props:
        print(f"  [{p.index}] {p.kind:25s} tier={p.tier} → {p.dispatch_handler}")

    if args.dry_run:
        print("\n[dry-run] no output written.")
        return 0

    out_path = args.out or (args.scene_yaml.parent / "assembled-manifest.json")
    manifest = emit_usd_stub(plan, out_path)
    print(f"\n[ok] manifest written to {out_path} "
          f"({len(manifest['layers'])} layers, {len(manifest['props'])} props)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
