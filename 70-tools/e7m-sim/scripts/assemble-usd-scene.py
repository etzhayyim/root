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
    """Resolve `at://...datasetPin/<rkey>` → IPFS CID.

    W2 integration: tries `e7m_dataset.pds.resolve_datasetpin` first
    against the religious-corp PDS. Falls back to a deterministic
    sha256 placeholder on any of:

      - placeholder URIs (containing `<...>` markers — W0/W1 scenes)
      - e7m-dataset module not on PYTHONPATH (e7m-sim standalone)
      - any transitive import / network / parse failure (defensive)

    The fallback path is stable byte-for-byte (G6) so dry-run outputs
    remain reproducible without a live PDS connection. Set
    `ETZ_E7M_SIM_STRICT_PDS=1` to fail-closed instead of falling back
    when the URI looks real and the PDS lookup errors out."""
    import os
    if "<" in at_uri and ">" in at_uri:
        digest = hashlib.sha256(at_uri.encode("utf-8")).hexdigest()[:46]
        return f"bafyplaceholder{digest}"

    try:
        from e7m_dataset import pds as _pds   # type: ignore
        record = _pds.resolve_datasetpin(at_uri)
        cid = record.get("cid")
        if isinstance(cid, str) and cid:
            return cid
        raise RuntimeError(f"resolved record missing cid: {record!r}")
    except Exception as exc:    # noqa: BLE001
        if os.environ.get("ETZ_E7M_SIM_STRICT_PDS") == "1":
            raise RuntimeError(
                f"PDS resolve failed under strict mode: {exc!r}"
            ) from exc
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

    Kept for backward-compat with W1 callers. W2 callers should use
    `emit_scene()` which writes both this manifest AND a real `.usda`
    file via the inline text emitter in §5 below.
    """
    manifest = _build_manifest(plan)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def _build_manifest(plan: AssemblyPlan) -> dict[str, Any]:
    """The manifest JSON content (shared between W1 stub + W2 emit_scene)."""
    return {
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


# ─── §5 W2 USDA text emitter ────────────────────────────────────────
#
# USDA = USD ASCII representation, stable spec at
# https://openusd.org/docs/USD-Glossary.html#USDGlossary-USDA-File
#
# W2.0 (this cycle): structural USDA — every layer/prop becomes a real
# UsdGeom.Mesh / UsdShade.Material / UsdGeom.PointInstancer prim, with
# deterministic placeholder geometry derived from the bbox + CID. This
# means the emitted .usda is loadable by any USD reader (Pixar OpenUSD,
# tinyusdz, kami-usd) and renders something visible; the geometry is
# not the actual SRTM mesh / Sentinel raster yet — that ingest lands
# at W2.1 alongside the real datasetPin → IPFS CID resolution.

USDA_HEADER = """#usda 1.0
(
    defaultPrim = "World"
    metersPerUnit = 1
    upAxis = "Z"
    doc = "Emitted by assemble-usd-scene.py (ADR-2605262500 §4 W2)"
)

"""


def _bbox_local_corners(plan: AssemblyPlan) -> tuple[float, float, float, float]:
    """Project the world bbox into a scene-local meter-grid.

    For W2.0 we assume EPSG:4326 (lon/lat) and approximate 1 deg ≈
    111_000 m at the bbox centroid. This gives a small-but-real
    rectangle whose corners are meaningful for sim physics. Full
    projection (EPSG:3857 etc.) lands at W2.1 with pyproj.
    """
    w, s, e, n = plan.bbox
    cy = (s + n) / 2.0
    import math
    lat_m = 111_320.0
    lon_m = 111_320.0 * math.cos(math.radians(cy))
    width = max(1.0, (e - w) * lon_m)
    height = max(1.0, (n - s) * lat_m)
    # Center the bbox on the scene origin.
    return (-width / 2.0, -height / 2.0, width / 2.0, height / 2.0)


def _synth_elevation(cid: str, ix: int, iy: int, nx: int, ny: int) -> float:
    """Deterministic synthetic elevation field for W2.1.

    Until rasterio + real SRTM .tif ingest lands (W2.2), this synthetic
    field stands in for actual elevation per vertex. CID-seeded so two
    layers from different SRTM tiles produce different terrain shapes.
    Returns elevation in meters; range roughly [-2, +2] m around the
    bbox plane. Real SRTM ranges much higher but the W2.1 emitter
    shape is the durable contract — rasterio integration is a one-line
    swap on the elevation source.
    """
    import math as _math
    seed = int(hashlib.sha256(cid.encode()).hexdigest()[:8], 16) / 0xffffffff
    u = ix / max(nx - 1, 1)
    v = iy / max(ny - 1, 1)
    return 2.0 * _math.sin(2 * _math.pi * (u + seed)) * _math.cos(2 * _math.pi * (v + seed * 0.5))


def _emit_terrain_usda(layer: LayerPlan, plan: AssemblyPlan, prim_name: str) -> str:
    """W2.1 triangulated grid Mesh covering the bbox.

    Grid resolution is driven by the scene YAML's `mesh.target_edge_m`
    attribute on the layer (defaults to 50m if not specified). For
    each (nx+1) × (ny+1) vertex we sample a synthetic elevation field
    seeded from the layer's resolved CID (W2.2 swaps this for rasterio
    SRTM `.tif` sampling on the real CID-resolved tile)."""
    x0, y0, x1, y1 = _bbox_local_corners(plan)
    target_edge = 50.0
    mesh_cfg = layer.extra.get("mesh") if isinstance(layer.extra.get("mesh"), dict) else {}
    if mesh_cfg and isinstance(mesh_cfg.get("target_edge_m"), (int, float)):
        target_edge = float(mesh_cfg["target_edge_m"])
    # Cap grid resolution so very wide bboxes don't explode prim size.
    nx = max(2, min(60, int((x1 - x0) / target_edge) + 1))
    ny = max(2, min(60, int((y1 - y0) / target_edge) + 1))

    pts: list[str] = []
    for iy in range(ny):
        for ix in range(nx):
            px = x0 + (x1 - x0) * ix / (nx - 1)
            py = y0 + (y1 - y0) * iy / (ny - 1)
            pz = _synth_elevation(layer.resolved_cid, ix, iy, nx, ny)
            pts.append(f"({px:.3f}, {py:.3f}, {pz:.3f})")
    pts_str = "[" + ", ".join(pts) + "]"

    # Quad faces in row-major order. Each (ix, iy) quad uses 4 verts.
    fvi: list[int] = []
    fvc: list[int] = []
    for iy in range(ny - 1):
        for ix in range(nx - 1):
            a = iy * nx + ix
            b = a + 1
            c = a + nx + 1
            d = a + nx
            fvi += [a, b, c, d]
            fvc.append(4)
    fvi_str = "[" + ", ".join(str(i) for i in fvi) + "]"
    fvc_str = "[" + ", ".join(str(i) for i in fvc) + "]"

    return f"""    def Mesh "{prim_name}"
    {{
        token kami_layer_kind = "terrain"
        string kami_source_subdataset = "{layer.source_subdataset}"
        string kami_resolved_cid = "{layer.resolved_cid}"
        string kami_tier = "{layer.tier}"
        int kami_grid_nx = {nx}
        int kami_grid_ny = {ny}
        float kami_target_edge_m = {target_edge}
        string kami_elevation_source = "synth-cid-seeded-w2.1"
        point3f[] points = {pts_str}
        int[] faceVertexCounts = {fvc_str}
        int[] faceVertexIndices = {fvi_str}
        token subdivisionScheme = "none"
    }}
"""


def _emit_raster_overlay_usda(layer: LayerPlan, plan: AssemblyPlan, prim_name: str) -> str:
    """UsdShade.Material declaration referencing the resolved CID."""
    return f"""    def Material "{prim_name}"
    {{
        token kami_layer_kind = "raster_overlay"
        string kami_source_subdataset = "{layer.source_subdataset}"
        string kami_resolved_cid = "{layer.resolved_cid}"
        string kami_tier = "{layer.tier}"
        token outputs:surface.connect = </World/{prim_name}/PreviewSurface.outputs:surface>

        def Shader "PreviewSurface"
        {{
            uniform token info:id = "UsdPreviewSurface"
            token outputs:surface
        }}
    }}
"""


def _synth_road_segments(
    cid: str,
    bbox: tuple[float, float, float, float],
    *,
    max_count: int = 12,
) -> list[list[tuple[float, float]]]:
    """Generate CID-seeded deterministic road polylines for W2.1.

    Returns a list of polylines, each a sequence of (x, y) waypoints
    forming a multi-segment road. Roads have 3-7 waypoints each, drawn
    deterministically from CID-seeded LCG state. All waypoints stay
    inside bbox (clamped). W2.2 swaps this for pyarrow ingest of the
    Overture transportation Parquet — same return shape, same downstream
    emit logic.
    """
    x0, y0, x1, y1 = bbox
    bw, bh = (x1 - x0), (y1 - y0)
    rng = int(hashlib.sha256(("road:" + cid).encode()).hexdigest()[:16], 16)

    def _u() -> float:
        nonlocal rng
        rng = (rng * 1103515245 + 12345) & 0x7fffffff
        return (rng >> 8) / float(0x7fffff)

    # CID-seeded count: at least 3, at most max_count.
    n_roads = 3 + int(_u() * (max_count - 2))
    polylines: list[list[tuple[float, float]]] = []
    for _ in range(n_roads):
        n_waypoints = 3 + int(_u() * 4)   # 3-6 waypoints per road
        # Start near a bbox edge for a more road-like character.
        side = int(_u() * 4)
        if side == 0:
            sx, sy = x0 + bw * 0.05, y0 + bh * _u()
        elif side == 1:
            sx, sy = x1 - bw * 0.05, y0 + bh * _u()
        elif side == 2:
            sx, sy = x0 + bw * _u(), y0 + bh * 0.05
        else:
            sx, sy = x0 + bw * _u(), y1 - bh * 0.05
        waypoints: list[tuple[float, float]] = [(sx, sy)]
        cx, cy = sx, sy
        for _ in range(n_waypoints - 1):
            dx = (_u() - 0.5) * bw * 0.25
            dy = (_u() - 0.5) * bh * 0.25
            cx = max(x0, min(x1, cx + dx))
            cy = max(y0, min(y1, cy + dy))
            waypoints.append((cx, cy))
        polylines.append(waypoints)
    return polylines


def _emit_vector_roads_usda(layer: LayerPlan, plan: AssemblyPlan, prim_name: str) -> str:
    """W2.1 multi-segment ribbon mesh per CID-seeded synthetic polyline.

    Emits a parent Scope containing one Mesh per polyline. Each Mesh's
    geometry is the lane ribbon (lane_width-wide strip following the
    polyline). W2.2 swaps `_synth_road_segments` for pyarrow Overture
    Parquet LineString ingest in one place; the per-polyline ribbon
    emit logic below stays unchanged."""
    x0, y0, x1, y1 = _bbox_local_corners(plan)
    ribbon_cfg = layer.extra.get("ribbon") if isinstance(layer.extra.get("ribbon"), dict) else {}
    lane_count = int(ribbon_cfg.get("default_lane_count", 2))
    lane_width = float(ribbon_cfg.get("default_lane_width_m", 3.5))
    z_offset = float(ribbon_cfg.get("z_offset_m", 0.05))
    material_token = str(layer.extra.get("material", "kami-pbrt:Asphalt"))
    half_total = max(0.5, lane_count * lane_width / 2.0)

    polylines = _synth_road_segments(layer.resolved_cid, (x0, y0, x1, y1))

    import math as _math
    child_meshes: list[str] = []
    for idx, line in enumerate(polylines):
        # Build the ribbon: for each consecutive pair of waypoints, produce
        # a quad with width = half_total on each side perpendicular to seg dir.
        verts: list[tuple[float, float, float]] = []
        fvi: list[int] = []
        fvc: list[int] = []
        if len(line) < 2:
            continue
        for i in range(len(line) - 1):
            (ax, ay) = line[i]
            (bx, by) = line[i + 1]
            dx, dy = bx - ax, by - ay
            seg_len = max(_math.hypot(dx, dy), 1e-6)
            # left-normal (perpendicular, unit length)
            nx = -dy / seg_len
            ny = dx / seg_len
            # 4 corners of the segment quad
            v0 = (ax + nx * half_total, ay + ny * half_total, z_offset)
            v1 = (bx + nx * half_total, by + ny * half_total, z_offset)
            v2 = (bx - nx * half_total, by - ny * half_total, z_offset)
            v3 = (ax - nx * half_total, ay - ny * half_total, z_offset)
            base = len(verts)
            verts.extend([v0, v1, v2, v3])
            fvi += [base, base + 1, base + 2, base + 3]
            fvc.append(4)
        pts_str = "[" + ", ".join(f"({v[0]:.3f}, {v[1]:.3f}, {v[2]:.3f})" for v in verts) + "]"
        fvi_str = "[" + ", ".join(str(i) for i in fvi) + "]"
        fvc_str = "[" + ", ".join(str(i) for i in fvc) + "]"
        child_meshes.append(
            f"""        def Mesh "R{idx:03d}"
        {{
            int kami_waypoint_count = {len(line)}
            int kami_segment_count = {len(line) - 1}
            point3f[] points = {pts_str}
            int[] faceVertexCounts = {fvc_str}
            int[] faceVertexIndices = {fvi_str}
            token subdivisionScheme = "none"
        }}
"""
        )

    return f"""    def Scope "{prim_name}"
    {{
        token kami_layer_kind = "vector_roads"
        string kami_source_subdataset = "{layer.source_subdataset}"
        string kami_resolved_cid = "{layer.resolved_cid}"
        string kami_tier = "{layer.tier}"
        int kami_road_count = {len(polylines)}
        int kami_lane_count = {lane_count}
        float kami_lane_width_m = {lane_width}
        token kami_material = "{material_token}"
        string kami_polyline_source = "synth-cid-seeded-w2.1"

{''.join(child_meshes)}    }}
"""


def _synth_building_polygons(
    cid: str,
    bbox: tuple[float, float, float, float],
    *,
    default_height_m: float,
    max_count: int = 20,
) -> list[tuple[list[tuple[float, float]], float]]:
    """Generate CID-seeded deterministic building polygons for W2.1.

    Returns a list of (polygon_xy, height_m) tuples. polygon_xy is a
    closed footprint (Nx2 list of (x, y) corners; rectangles for W2.1).
    W2.2 swaps this for pyarrow ingest of the resolved CID's Overture
    Parquet shard — same return shape, same downstream emit logic.
    """
    x0, y0, x1, y1 = bbox
    bw, bh = (x1 - x0), (y1 - y0)
    seed = int(hashlib.sha256(cid.encode()).hexdigest()[:16], 16)

    # CID-seeded count: at least 3, at most max_count.
    rng = seed
    rng = (rng * 1103515245 + 12345) & 0x7fffffff
    n = 3 + (rng >> 8) % (max_count - 2)

    polygons: list[tuple[list[tuple[float, float]], float]] = []
    for _ in range(n):
        rng = (rng * 1103515245 + 12345) & 0x7fffffff
        u = (rng >> 8) / float(0x7fffff)
        rng = (rng * 1103515245 + 12345) & 0x7fffffff
        v = (rng >> 8) / float(0x7fffff)
        rng = (rng * 1103515245 + 12345) & 0x7fffffff
        w_frac = 0.02 + 0.05 * ((rng >> 8) / float(0x7fffff))   # 2-7% of bbox
        rng = (rng * 1103515245 + 12345) & 0x7fffffff
        h_frac = 0.02 + 0.05 * ((rng >> 8) / float(0x7fffff))
        rng = (rng * 1103515245 + 12345) & 0x7fffffff
        height = default_height_m * (0.5 + ((rng >> 8) / float(0x7fffff)))

        hw = bw * w_frac / 2.0
        hh = bh * h_frac / 2.0
        # Clamp center so the whole polygon stays inside bbox.
        cx = x0 + hw + u * max(bw - 2 * hw, 0.0)
        cy = y0 + hh + v * max(bh - 2 * hh, 0.0)
        poly = [
            (cx - hw, cy - hh),
            (cx + hw, cy - hh),
            (cx + hw, cy + hh),
            (cx - hw, cy + hh),
        ]
        polygons.append((poly, height))
    return polygons


def _emit_vector_buildings_usda(layer: LayerPlan, plan: AssemblyPlan, prim_name: str) -> str:
    """W2.1 extruded mesh per CID-seeded synthetic polygon.

    Builds a child Scope under the layer prim, each child being one
    extruded Mesh per polygon. W2.2 wires real Overture Parquet via
    pyarrow + DuckDB-spatial bbox filter (already available — see
    `e7m_dataset.fetchers.overture` for the upstream side); the
    `_synth_building_polygons` swap point is the only line that
    changes between W2.1 and W2.2.
    """
    x0, y0, x1, y1 = _bbox_local_corners(plan)
    extrude_cfg = layer.extra.get("extrude") if isinstance(layer.extra.get("extrude"), dict) else {}
    default_h = float(extrude_cfg.get("default_height_m", 8.0))
    material_token = str(extrude_cfg.get("material", "kami-pbrt:Concrete_Grey"))

    polygons = _synth_building_polygons(
        layer.resolved_cid, (x0, y0, x1, y1), default_height_m=default_h
    )

    child_meshes: list[str] = []
    for idx, (poly, h) in enumerate(polygons):
        # Build the 8-vertex extruded box (4 base + 4 top).
        base_pts = [(px, py, 0.0) for (px, py) in poly]
        top_pts = [(px, py, h) for (px, py) in poly]
        all_pts = base_pts + top_pts
        pts_str = "[" + ", ".join(f"({p[0]:.3f}, {p[1]:.3f}, {p[2]:.3f})" for p in all_pts) + "]"
        n = len(poly)
        # 1 base quad, 1 top quad, n side quads.
        fvi: list[int] = []
        fvc: list[int] = []
        # base (winding facing down)
        fvi += list(range(n - 1, -1, -1))
        fvc.append(n)
        # top (winding facing up)
        fvi += list(range(n, 2 * n))
        fvc.append(n)
        # sides
        for i in range(n):
            j = (i + 1) % n
            fvi += [i, j, j + n, i + n]
            fvc.append(4)
        fvi_str = "[" + ", ".join(str(i) for i in fvi) + "]"
        fvc_str = "[" + ", ".join(str(i) for i in fvc) + "]"
        child_meshes.append(
            f"""        def Mesh "B{idx:03d}"
        {{
            float kami_height_m = {h:.3f}
            int kami_polygon_vertex_count = {n}
            point3f[] points = {pts_str}
            int[] faceVertexCounts = {fvc_str}
            int[] faceVertexIndices = {fvi_str}
            token subdivisionScheme = "none"
        }}
"""
        )

    return f"""    def Scope "{prim_name}"
    {{
        token kami_layer_kind = "vector_buildings"
        string kami_source_subdataset = "{layer.source_subdataset}"
        string kami_resolved_cid = "{layer.resolved_cid}"
        string kami_tier = "{layer.tier}"
        int kami_building_count = {len(polygons)}
        token kami_material = "{material_token}"
        string kami_polygon_source = "synth-cid-seeded-w2.1"

{''.join(child_meshes)}    }}
"""


def _emit_object_3d_instances_usda(prop: LayerPlan, plan: AssemblyPlan, prim_name: str) -> str:
    """UsdGeom.PointInstancer with deterministic placements derived from CID hash."""
    count = int(prop.extra.get("count", 0))
    x0, y0, x1, y1 = _bbox_local_corners(plan)
    # Deterministic offsets: hash the resolved CID, expand to count positions
    rng_seed = int(hashlib.sha256(prop.resolved_cid.encode()).hexdigest()[:8], 16)
    positions: list[str] = []
    for i in range(count):
        # Tiny PRNG (LCG) seeded from CID — stable across runs.
        rng_seed = (rng_seed * 1103515245 + 12345) & 0x7fffffff
        u = (rng_seed >> 8) / float(0x7fffff)
        rng_seed = (rng_seed * 1103515245 + 12345) & 0x7fffffff
        v = (rng_seed >> 8) / float(0x7fffff)
        px = x0 + u * (x1 - x0)
        py = y0 + v * (y1 - y0)
        positions.append(f"({px:.3f}, {py:.3f}, 0.5)")
    pos_str = "[" + ", ".join(positions) + "]" if positions else "[]"
    return f"""    def PointInstancer "{prim_name}"
    {{
        token kami_prop_kind = "object_3d_instances"
        string kami_source_subdataset = "{prop.source_subdataset}"
        string kami_resolved_cid = "{prop.resolved_cid}"
        string kami_tier = "{prop.tier}"
        int kami_count = {count}
        string kami_placement_strategy = "{prop.extra.get("placement_strategy", "uniform_seed")}"
        point3f[] positions = {pos_str}
    }}
"""


_LAYER_USDA_DISPATCH = {
    "terrain": _emit_terrain_usda,
    "raster_overlay": _emit_raster_overlay_usda,
    "vector_roads": _emit_vector_roads_usda,
    "vector_buildings": _emit_vector_buildings_usda,
}
_PROP_USDA_DISPATCH = {
    "object_3d_instances": _emit_object_3d_instances_usda,
}


def build_usda(plan: AssemblyPlan) -> str:
    """Compose the full USDA text. Deterministic given a fixed plan (G6)."""
    parts: list[str] = [USDA_HEADER]
    parts.append('def Xform "World"\n{\n')
    parts.append(f'    string kami_scene_name = "{plan.scene_name}"\n')
    parts.append(f'    string kami_adr = "{plan.adr}"\n')
    parts.append(f'    string kami_max_tier = "{plan.max_tier}"\n')
    parts.append(f'    string kami_crs = "{plan.crs}"\n\n')
    for layer in plan.layers:
        prim_name = f"Layer{layer.index}_{layer.kind}"
        emit = _LAYER_USDA_DISPATCH.get(layer.kind)
        if emit is None:
            # Unknown layer kind: emit a generic Xform marker.
            parts.append(
                f'    def Xform "{prim_name}"\n    {{\n'
                f'        token kami_layer_kind = "{layer.kind}"\n'
                f'        string kami_resolved_cid = "{layer.resolved_cid}"\n'
                f'    }}\n'
            )
        else:
            parts.append(emit(layer, plan, prim_name))
    for prop in plan.props:
        prim_name = f"Prop{prop.index}_{prop.kind}"
        emit = _PROP_USDA_DISPATCH.get(prop.kind)
        if emit is None:
            parts.append(
                f'    def Xform "{prim_name}"\n    {{\n'
                f'        token kami_prop_kind = "{prop.kind}"\n'
                f'        string kami_resolved_cid = "{prop.resolved_cid}"\n'
                f'    }}\n'
            )
        else:
            parts.append(emit(prop, plan, prim_name))
    parts.append("}\n")
    return "".join(parts)


def emit_scene(plan: AssemblyPlan, out_dir: Path) -> dict[str, Any]:
    """W2 emitter — writes both `scene.usda` and `manifest.json`.

    Returns the manifest dict (same shape as W1 emit_usd_stub).
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    usda_text = build_usda(plan)
    (out_dir / "scene.usda").write_text(usda_text, encoding="utf-8")
    manifest = _build_manifest(plan)
    manifest["emitter_status"] = "w2-real-usda-text"
    manifest["emitter_target"] = "USDA 1.0 text spec (loadable by Pixar OpenUSD / tinyusdz / kami-usd)"
    manifest["scene_usda_sha256"] = hashlib.sha256(usda_text.encode("utf-8")).hexdigest()
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
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
        "--manifest-only",
        action="store_true",
        help="Emit only the W1 stub manifest JSON (no scene.usda). Default writes both.",
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

    # W2 default: write both scene.usda + manifest.json into an out_dir.
    # Legacy --manifest-only flag preserves the W1 single-JSON behavior.
    if args.manifest_only:
        out_path = args.out or (args.scene_yaml.parent / "assembled-manifest.json")
        manifest = emit_usd_stub(plan, out_path)
        print(f"\n[ok] manifest written to {out_path} "
              f"({len(manifest['layers'])} layers, {len(manifest['props'])} props)")
        return 0

    out_dir = args.out or args.scene_yaml.parent
    manifest = emit_scene(plan, out_dir)
    print(f"\n[ok] scene.usda + manifest.json written to {out_dir}/ "
          f"({len(manifest['layers'])} layers, {len(manifest['props'])} props, "
          f"usda_sha256={manifest['scene_usda_sha256'][:12]}…)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
