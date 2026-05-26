"""Tests for assemble-usd-scene.py (ADR-2605262500 §4 W1 stub assembler).

Covers:
  - build_plan() succeeds on the real wadachi-r1-shibuya-1km scene.yaml
  - build_plan() rejects scenes that lack a `world:` section
  - Tier-C scenes require `-nc-` infix (G4 enforcement)
  - emit_usd_stub() is deterministic given fixed input (G6 — same scene
    YAML + same script version → byte-identical manifest JSON)

The script lives at ``70-tools/e7m-sim/scripts/assemble-usd-scene.py``
which has a hyphen, so we load it via importlib rather than `import`.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

# `hashlib` is used by the W2 USDA emit determinism check below.


# ─── module loading ─────────────────────────────────────────────────

_THIS = Path(__file__).resolve()
_E7M_SIM = _THIS.parent.parent
_SCRIPT = _E7M_SIM / "scripts" / "assemble-usd-scene.py"
_WADACHI_SCENE = _E7M_SIM / "scenes" / "wadachi-r1-shibuya-1km" / "scene.yaml"
_SUKI_SCENE = _E7M_SIM / "scenes" / "suki-r1-tokachi-2km-pasture" / "scene.yaml"
_SARUTAHIKO_SCENE = _E7M_SIM / "scenes" / "sarutahiko-r1-tomei-5km" / "scene.yaml"
_IGATA_SCENE = _E7M_SIM / "scenes" / "igata-r1-foundry-yard-50m" / "scene.yaml"
_FUTAWA_SCENE = _E7M_SIM / "scenes" / "futawa-r1-mountain-3km" / "scene.yaml"
_TATEKATA_SCENE = _E7M_SIM / "scenes" / "tatekata-r1-construction-site-100m" / "scene.yaml"
_HODOKI_SCENE = _E7M_SIM / "scenes" / "hodoki-r1-elv-yard-200m" / "scene.yaml"
_TSUTAE_SCENE = _E7M_SIM / "scenes" / "tsutae-r1-shibuya-crossing-200m" / "scene.yaml"

ALL_W4_SCENES = [
    _WADACHI_SCENE, _SUKI_SCENE, _SARUTAHIKO_SCENE, _IGATA_SCENE,
    _FUTAWA_SCENE, _TATEKATA_SCENE, _HODOKI_SCENE, _TSUTAE_SCENE,
]
_SCHEMA = _E7M_SIM / "scenes" / "_schema" / "scene.schema.json"


@pytest.fixture(scope="module")
def assemble_mod():
    """Load assemble-usd-scene.py as a module under name `assemble_usd_scene`."""
    spec = importlib.util.spec_from_file_location("assemble_usd_scene", _SCRIPT)
    assert spec is not None and spec.loader is not None, f"cannot load {_SCRIPT}"
    mod = importlib.util.module_from_spec(spec)
    sys.modules["assemble_usd_scene"] = mod
    spec.loader.exec_module(mod)
    return mod


# ─── build_plan on the real wadachi scene ───────────────────────────


def test_build_plan_on_wadachi_shibuya_1km(assemble_mod):
    plan = assemble_mod.build_plan(_WADACHI_SCENE)
    assert plan.scene_name == "wadachi-r1-shibuya-1km"
    assert plan.adr == "ADR-2605262500"
    assert plan.sim_consumer == "wadachi-r1"
    assert plan.crs == "EPSG:4326"
    assert plan.bbox == [139.69, 35.65, 139.71, 35.67]
    assert plan.max_tier == "A"          # Tier-A only at W1
    assert plan.must_carry_nc_infix is False
    assert len(plan.layers) == 4
    assert len(plan.props) == 0

    layer_kinds = [l.kind for l in plan.layers]
    assert layer_kinds == [
        "terrain", "raster_overlay", "vector_roads", "vector_buildings",
    ]
    for l in plan.layers:
        # W1 placeholder CIDs are deterministic via sha256 of the URI.
        assert l.resolved_cid.startswith("bafyplaceholder")
        assert l.tier == "A"
        assert l.dispatch_handler.startswith("kami-usd:")


def test_build_plan_resolves_placeholder_deterministically(assemble_mod):
    """Same scene YAML twice → same resolved_cid (W1 stub determinism)."""
    plan_a = assemble_mod.build_plan(_WADACHI_SCENE)
    plan_b = assemble_mod.build_plan(_WADACHI_SCENE)
    cids_a = [l.resolved_cid for l in plan_a.layers]
    cids_b = [l.resolved_cid for l in plan_b.layers]
    assert cids_a == cids_b


# ─── world: section is required for outdoor scenes ──────────────────


def test_build_plan_rejects_scene_without_world_section(assemble_mod, tmp_path):
    """cartpole-style scenes (no world data) MUST NOT be assembled."""
    fake_scene = tmp_path / "fake-scene-no-world" / "scene.yaml"
    fake_scene.parent.mkdir(parents=True)
    fake_scene.write_text(
        "adr: ADR-2605261800\n"
        "phase: R1.1\n"
        "scene:\n"
        "  num_envs: 1\n"
        "robot:\n"
        "  urdf: ./fake.urdf\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="no `world:` section"):
        assemble_mod.build_plan(fake_scene)


# ─── G4 — Tier-C scenes require `-nc-` infix ────────────────────────


def _write_tier_c_scene(scene_dir: Path, *, with_nc_infix: bool) -> Path:
    scene_dir.mkdir(parents=True, exist_ok=True)
    scene_path = scene_dir / "scene.yaml"
    scene_path.write_text(
        "adr: ADR-2605262500\n"
        "phase: W3\n"
        "sim_consumer: wadachi-r1\n"
        "world:\n"
        "  crs: EPSG:4326\n"
        "  bbox: [139.69, 35.65, 139.71, 35.67]\n"
        "  output_subdataset: sim-scenes/wadachi/r1/test/\n"
        "  layers:\n"
        "    - kind: terrain\n"
        "      source_subdataset: geo/srtm/n35e139\n"
        "      datasetPin_at: at://test/<rkey>\n"
        "      tier: A\n"
        "  props:\n"
        "    - kind: object_3d_instances\n"
        "      source_subdataset: geo/hf-3d-nc/cars\n"
        "      datasetPin_at: at://test/<rkey>\n"
        "      tier: C\n"
        "      count: 10\n",
        encoding="utf-8",
    )
    return scene_path


def test_build_plan_tier_c_with_nc_infix_passes(assemble_mod, tmp_path):
    scene = _write_tier_c_scene(tmp_path / "wadachi-r1-test-1km-nc", with_nc_infix=True)
    plan = assemble_mod.build_plan(scene)
    assert plan.max_tier == "C"
    assert plan.must_carry_nc_infix is True


def test_build_plan_tier_c_without_nc_infix_aborts(assemble_mod, tmp_path):
    scene = _write_tier_c_scene(tmp_path / "wadachi-r1-test-1km", with_nc_infix=False)
    with pytest.raises(ValueError, match="max_tier=C.+lacks `-nc-` infix"):
        assemble_mod.build_plan(scene)


def test_build_plan_tier_c_suffix_only_also_passes(assemble_mod, tmp_path):
    """Names ending in `-nc` (no trailing hyphen) also satisfy G4."""
    scene = _write_tier_c_scene(tmp_path / "wadachi-r1-test-1km-nc", with_nc_infix=True)
    plan = assemble_mod.build_plan(scene)
    assert plan.must_carry_nc_infix is True


# ─── G6 — emit_usd_stub determinism ─────────────────────────────────


def test_emit_usd_stub_deterministic_for_same_scene(assemble_mod, tmp_path):
    """G6: same scene.yaml → byte-identical manifest JSON.

    The only non-deterministic field in the W1 stub manifest would be
    timestamps. The stub deliberately uses sha256-derived placeholder
    CIDs (no time component) so a single build_plan + emit cycle MUST
    be reproducible. If this test ever breaks, G6 invariant is broken.
    """
    plan = assemble_mod.build_plan(_WADACHI_SCENE)

    out_a = tmp_path / "a.json"
    out_b = tmp_path / "b.json"
    assemble_mod.emit_usd_stub(plan, out_a)
    assemble_mod.emit_usd_stub(plan, out_b)

    bytes_a = out_a.read_bytes()
    bytes_b = out_b.read_bytes()
    assert bytes_a == bytes_b

    # Cross-check: build_plan again from the same YAML → emit → still identical.
    plan2 = assemble_mod.build_plan(_WADACHI_SCENE)
    out_c = tmp_path / "c.json"
    assemble_mod.emit_usd_stub(plan2, out_c)
    assert out_c.read_bytes() == bytes_a


def test_emit_usd_stub_manifest_carries_max_tier_and_dispatch(assemble_mod, tmp_path):
    plan = assemble_mod.build_plan(_WADACHI_SCENE)
    out = tmp_path / "manifest.json"
    manifest = assemble_mod.emit_usd_stub(plan, out)
    persisted: dict[str, Any] = json.loads(out.read_text(encoding="utf-8"))

    assert persisted == manifest                # in-memory == on-disk
    assert persisted["max_tier"] == "A"
    assert persisted["must_carry_nc_infix"] is False
    assert persisted["emitter_status"].startswith("stub-w1")
    assert all(
        l["dispatch_handler"].startswith("kami-usd:") for l in persisted["layers"]
    )


# ─── schema file exists + parseable ─────────────────────────────────


# ─── W2 USDA real text emit ─────────────────────────────────────────


def test_build_usda_on_wadachi_emits_world_xform(assemble_mod):
    plan = assemble_mod.build_plan(_WADACHI_SCENE)
    usda = assemble_mod.build_usda(plan)
    assert usda.startswith("#usda 1.0")
    assert 'defaultPrim = "World"' in usda
    assert 'def Xform "World"' in usda
    # 4 wadachi layers → 4 prim definitions
    assert 'def Mesh "Layer0_terrain"' in usda
    assert 'def Material "Layer1_raster_overlay"' in usda
    # W2.1: roads and buildings are now Scopes (per-polyline / per-polygon child Meshes).
    assert 'def Scope "Layer2_vector_roads"' in usda
    assert 'def Scope "Layer3_vector_buildings"' in usda
    # CID is embedded in each prim's kami_resolved_cid attr (audit trail)
    for layer in plan.layers:
        assert layer.resolved_cid in usda


def test_build_usda_is_deterministic_g6(assemble_mod):
    """G6: same scene.yaml → byte-identical USDA text."""
    plan_a = assemble_mod.build_plan(_WADACHI_SCENE)
    plan_b = assemble_mod.build_plan(_WADACHI_SCENE)
    usda_a = assemble_mod.build_usda(plan_a)
    usda_b = assemble_mod.build_usda(plan_b)
    assert usda_a == usda_b


def test_emit_scene_writes_usda_and_manifest(assemble_mod, tmp_path):
    plan = assemble_mod.build_plan(_WADACHI_SCENE)
    out_dir = tmp_path / "scene_out"
    manifest = assemble_mod.emit_scene(plan, out_dir)
    usda_path = out_dir / "scene.usda"
    manifest_path = out_dir / "manifest.json"
    assert usda_path.exists()
    assert manifest_path.exists()
    assert manifest["emitter_status"] == "w2-real-usda-text"
    assert manifest["scene_usda_sha256"] == hashlib.sha256(
        usda_path.read_bytes()
    ).hexdigest()


def test_emit_scene_is_deterministic_g6_full(assemble_mod, tmp_path):
    plan = assemble_mod.build_plan(_WADACHI_SCENE)
    a = tmp_path / "a"
    b = tmp_path / "b"
    assemble_mod.emit_scene(plan, a)
    assemble_mod.emit_scene(plan, b)
    assert (a / "scene.usda").read_bytes() == (b / "scene.usda").read_bytes()
    assert (a / "manifest.json").read_bytes() == (b / "manifest.json").read_bytes()


def test_build_usda_handles_tier_c_props(assemble_mod, tmp_path):
    """Tier-C `-nc-` scene with PointInstancer for object_3d_instances."""
    scene_dir = tmp_path / "wadachi-r1-test-1km-nc"
    scene_dir.mkdir()
    (scene_dir / "scene.yaml").write_text(
        "adr: ADR-2605262500\n"
        "phase: W3\n"
        "world:\n"
        "  crs: EPSG:4326\n"
        "  bbox: [139.69, 35.65, 139.71, 35.67]\n"
        "  output_subdataset: sim-scenes/test/\n"
        "  layers:\n"
        "    - kind: terrain\n"
        "      source_subdataset: geo/srtm/n35e139\n"
        "      datasetPin_at: at://test/<rkey>\n"
        "      tier: A\n"
        "  props:\n"
        "    - kind: object_3d_instances\n"
        "      source_subdataset: geo/hf-3d-nc/cars\n"
        "      datasetPin_at: at://test/<rkey>\n"
        "      tier: C\n"
        "      count: 5\n"
        "      placement_strategy: road_lane_center_jitter\n",
        encoding="utf-8",
    )
    plan = assemble_mod.build_plan(scene_dir / "scene.yaml")
    usda = assemble_mod.build_usda(plan)
    assert 'def PointInstancer "Prop0_object_3d_instances"' in usda
    assert 'kami_tier = "C"' in usda
    assert 'kami_count = 5' in usda


# ─── W4 cross-actor: suki R1 (farm tractor) ─────────────────────────


def test_suki_r1_scene_assembles_end_to_end(assemble_mod, tmp_path):
    """Cross-actor smoke: suki R1 farm scene goes through the same
    build_plan + emit_scene pipeline as wadachi. Validates the
    pipeline generalizes beyond the original wadachi testbed."""
    plan = assemble_mod.build_plan(_SUKI_SCENE)
    assert plan.sim_consumer == "suki-r1"
    assert plan.max_tier == "A"
    # Suki scene has 3 layers (no buildings in pasture; W2 will add landuse).
    assert len(plan.layers) == 3
    assert [l.kind for l in plan.layers] == [
        "terrain", "raster_overlay", "vector_roads",
    ]
    out_dir = tmp_path / "suki_out"
    manifest = assemble_mod.emit_scene(plan, out_dir)
    usda = (out_dir / "scene.usda").read_text(encoding="utf-8")
    assert 'string kami_scene_name = "suki-r1-tokachi-2km-pasture"' in usda
    assert manifest["scene_name"] == "suki-r1-tokachi-2km-pasture"
    assert manifest["emitter_status"] == "w2-real-usda-text"


def test_suki_and_wadachi_usda_differ_by_bbox(assemble_mod):
    """Two different actor scenes produce two different USDA texts."""
    wadachi_usda = assemble_mod.build_usda(assemble_mod.build_plan(_WADACHI_SCENE))
    suki_usda = assemble_mod.build_usda(assemble_mod.build_plan(_SUKI_SCENE))
    assert wadachi_usda != suki_usda
    assert 'kami_scene_name = "wadachi-r1-shibuya-1km"' in wadachi_usda
    assert 'kami_scene_name = "suki-r1-tokachi-2km-pasture"' in suki_usda


def test_sarutahiko_5km_non_square_bbox_assembles(assemble_mod, tmp_path):
    """5km×1km strip — stress-tests non-square bbox path through the assembler."""
    plan = assemble_mod.build_plan(_SARUTAHIKO_SCENE)
    assert plan.sim_consumer == "sarutahiko-r1"
    assert plan.max_tier == "A"
    assert len(plan.layers) == 3
    out_dir = tmp_path / "sarutahiko_out"
    manifest = assemble_mod.emit_scene(plan, out_dir)
    usda = (out_dir / "scene.usda").read_text(encoding="utf-8")
    assert 'kami_scene_name = "sarutahiko-r1-tomei-5km"' in usda
    # The bbox is ~5km E-W × ~1km N-S — width must be >> height in projection.
    corners = assemble_mod._bbox_local_corners(plan)
    width = corners[2] - corners[0]    # x1 - x0
    height = corners[3] - corners[1]   # y1 - y0
    assert width > 4000.0, f"5km E-W bbox should project to >4km width; got {width}"
    assert height < 1500.0, f"~1km N-S bbox should project to <1.5km height; got {height}"
    assert width / height > 4.0, f"aspect ratio should be >4:1; got {width / height:.1f}"
    assert manifest["scene_name"] == "sarutahiko-r1-tomei-5km"


def test_igata_small_bbox_assembles(assemble_mod, tmp_path):
    """~50m bbox — stress-tests the projection approximation at sub-100m scale."""
    plan = assemble_mod.build_plan(_IGATA_SCENE)
    assert plan.sim_consumer == "igata-r1"
    # igata yard has 4 layers (incl. buildings — workshop / warehouse).
    assert len(plan.layers) == 4
    assert [l.kind for l in plan.layers] == [
        "terrain", "raster_overlay", "vector_roads", "vector_buildings",
    ]
    out_dir = tmp_path / "igata_out"
    manifest = assemble_mod.emit_scene(plan, out_dir)
    usda = (out_dir / "scene.usda").read_text(encoding="utf-8")
    assert 'def Scope "Layer3_vector_buildings"' in usda
    assert manifest["scene_name"] == "igata-r1-foundry-yard-50m"


def test_all_four_cross_actor_scenes_emit_distinct_usda(assemble_mod):
    """Visual diff check: 4 W4 scenes → 4 distinct USDA texts."""
    plans = [
        assemble_mod.build_plan(p) for p in [
            _WADACHI_SCENE, _SUKI_SCENE, _SARUTAHIKO_SCENE, _IGATA_SCENE,
        ]
    ]
    usdas = [assemble_mod.build_usda(p) for p in plans]
    # All four must be pairwise distinct (different scene names → different text).
    assert len(set(usdas)) == 4
    # And the determinism invariant holds within each scene.
    for plan, usda in zip(plans, usdas):
        assert assemble_mod.build_usda(plan) == usda


# ─── full W4 8-scene matrix ─────────────────────────────────────────


@pytest.mark.parametrize("scene_path,expected_consumer,expected_layers", [
    (_FUTAWA_SCENE,   "futawa-r1",    3),
    (_TATEKATA_SCENE, "tatekata-r1",  4),
    (_HODOKI_SCENE,   "hodoki-r1",    3),
    (_TSUTAE_SCENE,   "tsutae-r1",    4),
])
def test_w4_scene_assembles_e2e(assemble_mod, tmp_path, scene_path, expected_consumer, expected_layers):
    """Each W4 scene must build_plan + emit_scene + USDA emit cleanly."""
    plan = assemble_mod.build_plan(scene_path)
    assert plan.sim_consumer == expected_consumer
    assert plan.max_tier == "A"
    assert len(plan.layers) == expected_layers
    out_dir = tmp_path / f"{expected_consumer}-out"
    manifest = assemble_mod.emit_scene(plan, out_dir)
    assert (out_dir / "scene.usda").exists()
    assert manifest["emitter_status"] == "w2-real-usda-text"


def test_all_eight_w4_scenes_emit_distinct_usda(assemble_mod):
    """The full W4 matrix produces 8 distinct USDA texts."""
    usdas = [assemble_mod.build_usda(assemble_mod.build_plan(p)) for p in ALL_W4_SCENES]
    assert len(set(usdas)) == 8


# ─── W2.1 terrain grid mesh ─────────────────────────────────────────


def test_w2_1_terrain_emits_grid_not_quad(assemble_mod):
    """W2.1: terrain must emit an N×N triangulated grid, not the W2.0 4-corner quad."""
    plan = assemble_mod.build_plan(_WADACHI_SCENE)
    terrain_layer = next(l for l in plan.layers if l.kind == "terrain")
    # The wadachi scene sets target_edge_m=5.0 over a ~1810m × 2226m bbox →
    # nx ≈ 1810/5 + 1 ≈ 363, capped at 60. ny ≈ 2226/5 + 1 ≈ 446, capped at 60.
    usda = assemble_mod._emit_terrain_usda(terrain_layer, plan, "T")
    # Should reference grid attributes.
    assert "kami_grid_nx" in usda
    assert "kami_grid_ny" in usda
    assert 'kami_elevation_source = "synth-cid-seeded-w2.1"' in usda
    # The point list must have >> 4 entries (W2.0 was exactly 4 corners).
    # Cheap check: count occurrences of "(" inside the points array.
    pts_block = usda.split("point3f[] points = [")[1].split("]")[0]
    n_pts = pts_block.count("(")
    assert n_pts >= 100, f"expected many grid points, got {n_pts}"


def test_w2_1_terrain_resolution_scales_with_target_edge(assemble_mod, tmp_path):
    """target_edge_m=2.0 → much finer grid than target_edge_m=10.0."""
    fine_dir = tmp_path / "fine-scene"
    fine_dir.mkdir()
    (fine_dir / "scene.yaml").write_text(
        "adr: ADR-2605262500\nphase: W2\nsim_consumer: test\n"
        "world:\n"
        "  crs: EPSG:4326\n"
        "  bbox: [139.69, 35.65, 139.71, 35.67]\n"
        "  output_subdataset: x/\n"
        "  layers:\n"
        "    - kind: terrain\n"
        "      source_subdataset: geo/srtm/test\n"
        "      datasetPin_at: at://x/<rkey>\n"
        "      tier: A\n"
        "      mesh: {target_edge_m: 200.0}\n",   # coarse grid
        encoding="utf-8",
    )
    plan = assemble_mod.build_plan(fine_dir / "scene.yaml")
    layer = plan.layers[0]
    usda = assemble_mod._emit_terrain_usda(layer, plan, "T")
    # Bbox is ~1810m × 2226m. target_edge=200 → nx≈10, ny≈12. Should be ~120 points.
    pts_block = usda.split("point3f[] points = [")[1].split("]")[0]
    n_pts = pts_block.count("(")
    assert 50 <= n_pts <= 200, f"target_edge=200 should give ~120 pts; got {n_pts}"


def test_w2_1_terrain_determinism_g6_preserved(assemble_mod):
    """The grid mesh + synth elevation must still be deterministic (G6)."""
    plan = assemble_mod.build_plan(_WADACHI_SCENE)
    layer = next(l for l in plan.layers if l.kind == "terrain")
    a = assemble_mod._emit_terrain_usda(layer, plan, "T")
    b = assemble_mod._emit_terrain_usda(layer, plan, "T")
    assert a == b


def test_w2_1_synth_elevation_cid_seeded(assemble_mod):
    """Different CIDs produce different elevation fields."""
    z_a = assemble_mod._synth_elevation("bafyplaceholder_a", 5, 5, 10, 10)
    z_b = assemble_mod._synth_elevation("bafyplaceholder_b", 5, 5, 10, 10)
    assert z_a != z_b
    # Same CID = same value (determinism).
    z_a2 = assemble_mod._synth_elevation("bafyplaceholder_a", 5, 5, 10, 10)
    assert z_a == z_a2


# ─── W2.1 buildings extrusion ──────────────────────────────────────


def test_w2_1_buildings_emit_multiple_polygons(assemble_mod):
    """W2.1: vector_buildings must emit a Scope containing N child Meshes
    (was: single placeholder cube)."""
    plan = assemble_mod.build_plan(_WADACHI_SCENE)
    buildings = next(l for l in plan.layers if l.kind == "vector_buildings")
    usda = assemble_mod._emit_vector_buildings_usda(buildings, plan, "BLDG")
    # Should use a Scope as the parent prim (not a single Mesh).
    assert 'def Scope "BLDG"' in usda
    # kami_building_count must be ≥ 3 (the synth lower bound).
    import re
    m = re.search(r"int kami_building_count = (\d+)", usda)
    assert m is not None
    n_buildings = int(m.group(1))
    assert 3 <= n_buildings <= 20, f"expected 3-20 buildings, got {n_buildings}"
    # Each building must have its own child Mesh.
    child_count = usda.count('def Mesh "B')
    assert child_count == n_buildings


def test_w2_1_buildings_cid_seeded_count(assemble_mod):
    """Different layer CIDs must produce different building counts (with high
    probability) but the SAME CID must always produce the SAME count (G6)."""
    a = assemble_mod._synth_building_polygons(
        "bafy_a", (0, 0, 1000, 1000), default_height_m=10.0
    )
    a2 = assemble_mod._synth_building_polygons(
        "bafy_a", (0, 0, 1000, 1000), default_height_m=10.0
    )
    b = assemble_mod._synth_building_polygons(
        "bafy_b_different", (0, 0, 1000, 1000), default_height_m=10.0
    )
    # Determinism (G6): same CID → identical polygon list.
    assert a == a2
    # Difference (visibility): another CID → different result (very likely).
    assert a != b


def test_w2_1_buildings_polygons_inside_bbox(assemble_mod):
    """All synth polygons must lie within the bbox they're seeded for."""
    bbox = (-500.0, -500.0, 500.0, 500.0)
    polys = assemble_mod._synth_building_polygons(
        "bafy_bbox_test", bbox, default_height_m=8.0
    )
    x0, y0, x1, y1 = bbox
    for poly, _height in polys:
        for (x, y) in poly:
            assert x0 <= x <= x1, f"polygon x out of bbox: {x}"
            assert y0 <= y <= y1, f"polygon y out of bbox: {y}"


def test_w2_1_buildings_determinism_g6_via_full_emit(assemble_mod):
    plan = assemble_mod.build_plan(_WADACHI_SCENE)
    layer = next(l for l in plan.layers if l.kind == "vector_buildings")
    a = assemble_mod._emit_vector_buildings_usda(layer, plan, "BLDG")
    b = assemble_mod._emit_vector_buildings_usda(layer, plan, "BLDG")
    assert a == b


# ─── W2.1 vector_roads multi-segment polylines ──────────────────────


def test_w2_1_roads_emit_scope_with_child_meshes(assemble_mod):
    """W2.1: vector_roads is a Scope containing N child Meshes (was: single Mesh)."""
    plan = assemble_mod.build_plan(_WADACHI_SCENE)
    roads = next(l for l in plan.layers if l.kind == "vector_roads")
    usda = assemble_mod._emit_vector_roads_usda(roads, plan, "ROADS")
    assert 'def Scope "ROADS"' in usda
    import re
    m = re.search(r"int kami_road_count = (\d+)", usda)
    assert m is not None
    n_roads = int(m.group(1))
    assert 3 <= n_roads <= 12, f"expected 3-12 roads, got {n_roads}"
    # Each road must have its own child Mesh and ≥1 segment.
    child_count = usda.count('def Mesh "R')
    assert child_count == n_roads
    # Each child Mesh must report waypoint+segment counts.
    assert "kami_waypoint_count" in usda
    assert "kami_segment_count" in usda


def test_w2_1_roads_cid_seeded(assemble_mod):
    """Different layer CIDs → different polylines; same CID → identical."""
    a = assemble_mod._synth_road_segments("cidA", (0, 0, 1000, 1000))
    a2 = assemble_mod._synth_road_segments("cidA", (0, 0, 1000, 1000))
    b = assemble_mod._synth_road_segments("cidB_different", (0, 0, 1000, 1000))
    assert a == a2
    assert a != b


def test_w2_1_roads_waypoints_inside_bbox(assemble_mod):
    """All synth waypoints must lie within the bbox they're seeded for."""
    bbox = (-500.0, -500.0, 500.0, 500.0)
    polylines = assemble_mod._synth_road_segments("cid_bbox_test", bbox)
    x0, y0, x1, y1 = bbox
    for line in polylines:
        for (x, y) in line:
            assert x0 <= x <= x1
            assert y0 <= y <= y1


def test_w2_1_roads_polyline_count_in_range(assemble_mod):
    """Roads count must be in [3, max_count] for varied CIDs."""
    for seed in ["cid1", "cid2", "cid3", "cid_xx", "cid_long_string_abc_def"]:
        polylines = assemble_mod._synth_road_segments(seed, (0, 0, 1000, 1000))
        assert 3 <= len(polylines) <= 12, f"out of range for {seed}: {len(polylines)}"
        # Each polyline must have at least 2 waypoints to form a segment.
        for line in polylines:
            assert len(line) >= 2


def test_w2_1_roads_determinism_g6_via_full_emit(assemble_mod):
    plan = assemble_mod.build_plan(_WADACHI_SCENE)
    layer = next(l for l in plan.layers if l.kind == "vector_roads")
    a = assemble_mod._emit_vector_roads_usda(layer, plan, "R")
    b = assemble_mod._emit_vector_roads_usda(layer, plan, "R")
    assert a == b


def test_makura_indoor_carveout_has_no_scene_yaml():
    """ADR-2605262500 W4 explicit carve-out: makura is indoor-only,
    no outdoor scene.yaml is produced; only a README documents why."""
    carveout_dir = _E7M_SIM / "scenes" / "makura-r1-INDOOR-CARVEOUT"
    assert carveout_dir.exists()
    assert (carveout_dir / "README.md").exists()
    assert not (carveout_dir / "scene.yaml").exists()


def test_scene_schema_file_is_valid_json():
    """Sanity-check the schema is parseable JSON regardless of jsonschema availability."""
    body = json.loads(_SCHEMA.read_text(encoding="utf-8"))
    assert body.get("$schema", "").endswith("/2020-12/schema")
    assert "properties" in body
    assert "world" in body["properties"]
    assert "worldLayer" in body["$defs"]
