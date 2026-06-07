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


# ─── W2.2 Overture Parquet ingest (pyarrow) ──────────────────────────


def _make_overture_buildings_parquet(path, rows):
    """Write a tiny Overture-shaped buildings Parquet via pyarrow.

    `rows` = list of dicts with bbox + height. Schema mirrors Overture's
    canonical buildings columns (subset).
    """
    import pyarrow as pa
    import pyarrow.parquet as pq
    bbox_struct = pa.struct([
        ("xmin", pa.float64()), ("xmax", pa.float64()),
        ("ymin", pa.float64()), ("ymax", pa.float64()),
    ])
    table = pa.table({
        "bbox": pa.array([r["bbox"] for r in rows], type=bbox_struct),
        "height": pa.array([r.get("height") for r in rows], type=pa.float64()),
    })
    pq.write_table(table, path)


def test_w2_2_load_overture_buildings_basic(assemble_mod, tmp_path):
    """Operator-staged Parquet → axis-aligned rectangle per row."""
    parquet = tmp_path / "buildings.parquet"
    _make_overture_buildings_parquet(parquet, [
        {"bbox": {"xmin": 139.695, "xmax": 139.696, "ymin": 35.655, "ymax": 35.656}, "height": 25.0},
        {"bbox": {"xmin": 139.700, "xmax": 139.701, "ymin": 35.660, "ymax": 35.661}, "height": 12.0},
        {"bbox": {"xmin": 139.705, "xmax": 139.706, "ymin": 35.665, "ymax": 35.666}, "height": 8.0},
    ])
    plan_bbox = (139.69, 35.65, 139.71, 35.67)
    polygons = assemble_mod._load_overture_buildings_parquet(
        parquet, plan_bbox, default_height_m=8.0
    )
    assert polygons is not None
    assert len(polygons) == 3
    # Each polygon must be a 4-corner closed rect.
    for poly, h in polygons:
        assert len(poly) == 4
        assert isinstance(h, float)
    # Heights round-tripped.
    heights = sorted(h for _poly, h in polygons)
    assert heights == [8.0, 12.0, 25.0]


def test_w2_2_load_overture_skips_rows_outside_bbox(assemble_mod, tmp_path):
    parquet = tmp_path / "buildings.parquet"
    _make_overture_buildings_parquet(parquet, [
        {"bbox": {"xmin": 0.0, "xmax": 1.0, "ymin": 0.0, "ymax": 1.0}, "height": 5.0},   # far away
        {"bbox": {"xmin": 139.700, "xmax": 139.701, "ymin": 35.660, "ymax": 35.661}, "height": 12.0},
        {"bbox": {"xmin": 200.0, "xmax": 201.0, "ymin": 35.0, "ymax": 36.0}, "height": 3.0},   # also far
    ])
    plan_bbox = (139.69, 35.65, 139.71, 35.67)
    polygons = assemble_mod._load_overture_buildings_parquet(
        parquet, plan_bbox, default_height_m=8.0
    )
    assert polygons is not None
    assert len(polygons) == 1
    assert polygons[0][1] == 12.0


def test_w2_2_load_overture_missing_file_returns_none(assemble_mod, tmp_path):
    polygons = assemble_mod._load_overture_buildings_parquet(
        tmp_path / "does-not-exist.parquet", (0, 0, 1, 1), default_height_m=8.0
    )
    assert polygons is None


def test_w2_2_load_overture_default_height_when_null(assemble_mod, tmp_path):
    parquet = tmp_path / "buildings.parquet"
    _make_overture_buildings_parquet(parquet, [
        {"bbox": {"xmin": 139.700, "xmax": 139.701, "ymin": 35.660, "ymax": 35.661}, "height": None},
    ])
    polygons = assemble_mod._load_overture_buildings_parquet(
        parquet, (139.69, 35.65, 139.71, 35.67), default_height_m=15.0
    )
    assert polygons is not None
    assert polygons[0][1] == 15.0   # fell back to default


# ─── W2.2 cont. — WKB LineString roads ──────────────────────────────


def _wkb_linestring_le(points: list[tuple[float, float]]) -> bytes:
    """Encode (x, y) waypoints as a little-endian WKB LineString."""
    import struct
    out = bytearray()
    out.append(1)                                          # little-endian
    out += struct.pack("<I", 2)                            # geometry type = LineString
    out += struct.pack("<I", len(points))                  # num points
    for x, y in points:
        out += struct.pack("<dd", x, y)
    return bytes(out)


def _wkb_point_le(x: float, y: float) -> bytes:
    """Encode a WKB Point — used to test the 'skip non-LineString' path."""
    import struct
    return bytes([1]) + struct.pack("<I", 1) + struct.pack("<dd", x, y)


def _make_overture_roads_parquet(path, rows: list[bytes]):
    """Write a tiny Overture-shaped transportation Parquet with WKB geometry."""
    import pyarrow as pa
    import pyarrow.parquet as pq
    table = pa.table({"geometry": pa.array(rows, type=pa.binary())})
    pq.write_table(table, path)


def test_w2_2_parse_wkb_linestring_basic(assemble_mod):
    """Encode 3 waypoints → decode round-trip."""
    pts = [(139.700, 35.660), (139.701, 35.661), (139.702, 35.660)]
    wkb = _wkb_linestring_le(pts)
    decoded = assemble_mod._parse_wkb_linestring(wkb)
    assert decoded == pts


def test_w2_2_parse_wkb_rejects_point(assemble_mod):
    """A WKB Point (geometry type 1) must be skipped."""
    decoded = assemble_mod._parse_wkb_linestring(_wkb_point_le(0.0, 0.0))
    assert decoded is None


def test_w2_2_parse_wkb_rejects_short_input(assemble_mod):
    assert assemble_mod._parse_wkb_linestring(b"") is None
    assert assemble_mod._parse_wkb_linestring(b"\x01\x02") is None


def test_w2_2_load_overture_roads_basic(assemble_mod, tmp_path):
    parquet = tmp_path / "roads.parquet"
    _make_overture_roads_parquet(parquet, [
        _wkb_linestring_le([(139.700, 35.660), (139.701, 35.661)]),
        _wkb_linestring_le([(139.702, 35.662), (139.703, 35.663), (139.704, 35.664)]),
        _wkb_point_le(139.705, 35.665),     # skipped (not LineString)
    ])
    polylines = assemble_mod._load_overture_roads_parquet(
        parquet, (139.69, 35.65, 139.71, 35.67)
    )
    assert polylines is not None
    assert len(polylines) == 2
    # The 3-waypoint road must survive intact.
    assert len(polylines[0]) == 2
    assert len(polylines[1]) == 3


def test_w2_2_load_overture_roads_skips_outside_bbox(assemble_mod, tmp_path):
    parquet = tmp_path / "roads.parquet"
    _make_overture_roads_parquet(parquet, [
        _wkb_linestring_le([(0.0, 0.0), (1.0, 1.0)]),                       # far away
        _wkb_linestring_le([(139.700, 35.660), (139.701, 35.661)]),         # inside
        _wkb_linestring_le([(200.0, 35.0), (201.0, 36.0)]),                 # far away
    ])
    polylines = assemble_mod._load_overture_roads_parquet(
        parquet, (139.69, 35.65, 139.71, 35.67)
    )
    assert polylines is not None
    assert len(polylines) == 1


def test_w2_2_load_overture_roads_missing_file_returns_none(assemble_mod, tmp_path):
    polylines = assemble_mod._load_overture_roads_parquet(
        tmp_path / "missing.parquet", (0, 0, 1, 1)
    )
    assert polylines is None


def test_w2_2_emit_roads_uses_parquet_when_layer_points_to_it(assemble_mod, tmp_path):
    parquet = tmp_path / "real-roads.parquet"
    _make_overture_roads_parquet(parquet, [
        _wkb_linestring_le([(139.700, 35.660), (139.701, 35.661), (139.702, 35.660)]),
        _wkb_linestring_le([(139.703, 35.663), (139.704, 35.664)]),
    ])
    scene_dir = tmp_path / "wadachi-r1-with-real-roads"
    scene_dir.mkdir()
    (scene_dir / "scene.yaml").write_text(
        "adr: ADR-2605262500\nphase: W2\nsim_consumer: test\n"
        "world:\n"
        "  crs: EPSG:4326\n"
        "  bbox: [139.69, 35.65, 139.71, 35.67]\n"
        "  output_subdataset: x/\n"
        "  layers:\n"
        "    - kind: terrain\n"
        "      source_subdataset: geo/srtm/test\n"
        "      datasetPin_at: at://test/<rkey>\n"
        "      tier: A\n"
        "    - kind: vector_roads\n"
        "      source_subdataset: geo/overture/transportation/test\n"
        "      datasetPin_at: at://test/<rkey>\n"
        "      tier: A\n"
        f"      local_parquet_path: {parquet}\n",
        encoding="utf-8",
    )
    plan = assemble_mod.build_plan(scene_dir / "scene.yaml")
    roads = next(l for l in plan.layers if l.kind == "vector_roads")
    usda = assemble_mod._emit_vector_roads_usda(roads, plan, "R")
    # 2 polylines in Parquet → 2 child Meshes.
    assert usda.count('def Mesh "R') == 2
    assert "overture-parquet-w2.2" in usda
    # Waypoint counts: 3-point line + 2-point line.
    assert "kami_waypoint_count = 3" in usda
    assert "kami_waypoint_count = 2" in usda


# ─── W2.3 WKB Polygon + MultiLineString ─────────────────────────────


def _wkb_polygon_le(rings: list[list[tuple[float, float]]]) -> bytes:
    """Encode a WKB Polygon with one or more rings (outer + holes)."""
    import struct
    out = bytearray()
    out.append(1)                          # little-endian
    out += struct.pack("<I", 3)            # Polygon
    out += struct.pack("<I", len(rings))
    for ring in rings:
        out += struct.pack("<I", len(ring))
        for x, y in ring:
            out += struct.pack("<dd", x, y)
    return bytes(out)


def _wkb_multilinestring_le(linestrings: list[list[tuple[float, float]]]) -> bytes:
    """Encode a WKB MultiLineString (embeds full sub-LineString records)."""
    import struct
    out = bytearray()
    out.append(1)
    out += struct.pack("<I", 5)            # MultiLineString
    out += struct.pack("<I", len(linestrings))
    for line in linestrings:
        out += _wkb_linestring_le(line)
    return bytes(out)


def test_w2_3_parse_wkb_polygon_outer_ring(assemble_mod):
    """3-vertex closed polygon (with explicit closing duplicate) → 3 unique pts."""
    ring = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0), (0.0, 0.0)]
    wkb = _wkb_polygon_le([ring])
    decoded = assemble_mod._parse_wkb_polygon_outer_ring(wkb)
    assert decoded == [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]


def test_w2_3_parse_wkb_polygon_drops_inner_rings(assemble_mod):
    outer = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0), (0.0, 0.0)]
    hole = [(2.0, 2.0), (3.0, 2.0), (3.0, 3.0), (2.0, 3.0), (2.0, 2.0)]
    wkb = _wkb_polygon_le([outer, hole])
    decoded = assemble_mod._parse_wkb_polygon_outer_ring(wkb)
    # Only outer ring, hole discarded.
    assert len(decoded) == 4
    assert (0.0, 0.0) in decoded


def test_w2_3_parse_wkb_polygon_rejects_linestring(assemble_mod):
    """A WKB LineString must not be accepted by the polygon decoder."""
    wkb = _wkb_linestring_le([(0.0, 0.0), (1.0, 1.0)])
    assert assemble_mod._parse_wkb_polygon_outer_ring(wkb) is None


def test_w2_3_parse_wkb_polygon_rejects_degenerate(assemble_mod):
    """Polygon with < 3 unique points → None."""
    ring = [(0.0, 0.0), (1.0, 0.0), (0.0, 0.0)]   # 2 unique after closing dedup
    wkb = _wkb_polygon_le([ring])
    assert assemble_mod._parse_wkb_polygon_outer_ring(wkb) is None


def test_w2_3_parse_wkb_multilinestring(assemble_mod):
    """3-segment MultiLineString → 3 polylines preserved."""
    lines = [
        [(0.0, 0.0), (1.0, 1.0)],
        [(2.0, 2.0), (3.0, 3.0), (4.0, 4.0)],
        [(5.0, 5.0), (6.0, 6.0)],
    ]
    wkb = _wkb_multilinestring_le(lines)
    decoded = assemble_mod._parse_wkb_multilinestring(wkb)
    assert decoded == lines


def test_w2_3_parse_wkb_multilinestring_rejects_linestring(assemble_mod):
    wkb = _wkb_linestring_le([(0.0, 0.0), (1.0, 1.0)])
    assert assemble_mod._parse_wkb_multilinestring(wkb) is None


# ─── W2.3 Parquet ingest paths ──────────────────────────────────────


def test_w2_3_buildings_polygon_takes_precedence_over_bbox(assemble_mod, tmp_path):
    """When `geometry` column has a real WKB Polygon, the emitted polygon
    has the polygon's actual corner count, not 4 (the bbox fallback)."""
    import pyarrow as pa
    import pyarrow.parquet as pq
    # Hexagon (6 corners) at known location.
    hex_ring = [
        (139.700, 35.660), (139.7005, 35.6603), (139.7005, 35.6607),
        (139.700, 35.661), (139.6995, 35.6607), (139.6995, 35.6603),
        (139.700, 35.660),
    ]
    bbox_struct = pa.struct([
        ("xmin", pa.float64()), ("xmax", pa.float64()),
        ("ymin", pa.float64()), ("ymax", pa.float64()),
    ])
    table = pa.table({
        "bbox": pa.array(
            [{"xmin": 139.6995, "xmax": 139.7005, "ymin": 35.660, "ymax": 35.661}],
            type=bbox_struct,
        ),
        "height": pa.array([15.0], type=pa.float64()),
        "geometry": pa.array([_wkb_polygon_le([hex_ring])], type=pa.binary()),
    })
    parquet = tmp_path / "buildings-with-geom.parquet"
    pq.write_table(table, parquet)
    polygons = assemble_mod._load_overture_buildings_parquet(
        parquet, (139.69, 35.65, 139.71, 35.67), default_height_m=8.0
    )
    assert polygons is not None
    assert len(polygons) == 1
    poly, h = polygons[0]
    # Hexagon outer ring → 6 corners (vs 4 for bbox fallback).
    assert len(poly) == 6
    assert h == 15.0


def test_w2_3_roads_multilinestring(assemble_mod, tmp_path):
    """A MultiLineString row expands into N polylines."""
    multi = _wkb_multilinestring_le([
        [(139.700, 35.660), (139.701, 35.661)],
        [(139.702, 35.662), (139.703, 35.663), (139.704, 35.664)],
    ])
    parquet = tmp_path / "roads-multi.parquet"
    _make_overture_roads_parquet(parquet, [multi])
    polylines = assemble_mod._load_overture_roads_parquet(
        parquet, (139.69, 35.65, 139.71, 35.67)
    )
    assert polylines is not None
    assert len(polylines) == 2
    assert len(polylines[0]) == 2
    assert len(polylines[1]) == 3


def test_w2_3_roads_mixed_linestring_and_multilinestring(assemble_mod, tmp_path):
    """Mixed Parquet (LineString + MultiLineString) — both contribute polylines."""
    parquet = tmp_path / "roads-mixed.parquet"
    _make_overture_roads_parquet(parquet, [
        _wkb_linestring_le([(139.700, 35.660), (139.701, 35.661)]),
        _wkb_multilinestring_le([
            [(139.702, 35.662), (139.703, 35.663)],
            [(139.704, 35.664), (139.705, 35.665)],
        ]),
        _wkb_point_le(139.706, 35.666),    # unknown type — silently skipped
    ])
    polylines = assemble_mod._load_overture_roads_parquet(
        parquet, (139.69, 35.65, 139.71, 35.67)
    )
    assert polylines is not None
    # 1 single + 2 multi-sub = 3 polylines (Point skipped).
    assert len(polylines) == 3


def test_w2_2_emit_uses_parquet_when_layer_points_to_it(assemble_mod, tmp_path):
    """When the layer extra carries `local_parquet_path`, emit uses real polygons."""
    parquet = tmp_path / "real-buildings.parquet"
    _make_overture_buildings_parquet(parquet, [
        {"bbox": {"xmin": 139.700, "xmax": 139.701, "ymin": 35.660, "ymax": 35.661}, "height": 18.0},
        {"bbox": {"xmin": 139.702, "xmax": 139.703, "ymin": 35.662, "ymax": 35.663}, "height": 22.0},
    ])
    # Build a scene yaml that references the parquet path under buildings layer extra.
    scene_dir = tmp_path / "wadachi-r1-with-real-parquet"
    scene_dir.mkdir()
    (scene_dir / "scene.yaml").write_text(
        "adr: ADR-2605262500\nphase: W2\nsim_consumer: test\n"
        "world:\n"
        "  crs: EPSG:4326\n"
        "  bbox: [139.69, 35.65, 139.71, 35.67]\n"
        "  output_subdataset: x/\n"
        "  layers:\n"
        "    - kind: terrain\n"
        "      source_subdataset: geo/srtm/test\n"
        "      datasetPin_at: at://test/<rkey>\n"
        "      tier: A\n"
        "    - kind: vector_buildings\n"
        "      source_subdataset: geo/overture/buildings/test\n"
        "      datasetPin_at: at://test/<rkey>\n"
        "      tier: A\n"
        f"      local_parquet_path: {parquet}\n",
        encoding="utf-8",
    )
    plan = assemble_mod.build_plan(scene_dir / "scene.yaml")
    buildings = next(l for l in plan.layers if l.kind == "vector_buildings")
    usda = assemble_mod._emit_vector_buildings_usda(buildings, plan, "BLDG")
    # Must have exactly 2 buildings (matches the 2 Parquet rows).
    assert usda.count('def Mesh "B') == 2
    # Polygon source must indicate Parquet ingest, not synth.
    assert "overture-parquet-w2.2" in usda
    # The 18m and 22m heights should appear.
    assert "kami_height_m = 18.000" in usda
    assert "kami_height_m = 22.000" in usda


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


# ─── W2.2 raster_overlay (Pillow GeoTIFF / PNG sidecar) ─────────────


def _make_test_image(path: Path, *, size: tuple[int, int] = (32, 24)) -> None:
    from PIL import Image
    import numpy as _np
    rng = _np.random.RandomState(99)
    arr = rng.randint(0, 256, size=(size[1], size[0], 3), dtype=_np.uint8)
    Image.fromarray(arr).save(path, format="PNG")


# ─── W2.2 terrain real elevation ingest ─────────────────────────────


def test_w2_2_load_elevation_image_round_trips(assemble_mod, tmp_path):
    """16-bit grayscale TIFF → numpy array sampled at target grid size."""
    import numpy as np
    from PIL import Image
    # Make a 32x32 grayscale gradient (uint16) — pretend elevation in meters.
    arr = np.zeros((32, 32), dtype=np.uint16)
    for y in range(32):
        for x in range(32):
            arr[y, x] = x * 100 + y * 50    # 0..3200+1550 range
    src = tmp_path / "dem.tif"
    Image.fromarray(arr, mode="I;16").save(src)

    out = assemble_mod._load_elevation_image(src, 8, 8)
    assert out is not None
    assert out.shape == (8, 8)
    # Corner values: (0,0) → arr[0,0] = 0; (7,7) → arr[31,31] = 31*100+31*50 = 4650
    assert out[0, 0] == 0.0
    assert out[7, 7] == pytest.approx(4650.0)


def test_w2_2_load_elevation_missing_file_returns_none(assemble_mod, tmp_path):
    out = assemble_mod._load_elevation_image(tmp_path / "no-such.tif", 4, 4)
    assert out is None


def test_w2_2_load_elevation_handles_rgb_via_mean(assemble_mod, tmp_path):
    """RGB image → grayscale mean across channels."""
    import numpy as np
    from PIL import Image
    arr = np.full((16, 16, 3), [60, 120, 180], dtype=np.uint8)
    src = tmp_path / "rgb.png"
    Image.fromarray(arr).save(src)
    out = assemble_mod._load_elevation_image(src, 4, 4)
    assert out is not None
    # All pixels = mean(60, 120, 180) = 120
    assert (out == 120.0).all()


def test_w2_4_rasterio_path_documented_but_pillow_fallback_works(assemble_mod, tmp_path):
    """W2.4 rasterio path is documented; this test verifies the Pillow
    fallback still works when rasterio is unavailable (current env) so
    operators without rasterio don't regress."""
    import numpy as np
    from PIL import Image
    arr = np.full((16, 16), 300, dtype=np.uint16)
    p = tmp_path / "dem-no-rasterio.tif"
    Image.fromarray(arr, mode="I;16").save(p)
    out = assemble_mod._load_elevation_image(
        p, 4, 4, plan_bbox=(139.69, 35.65, 139.71, 35.67),
    )
    # Without rasterio, Pillow path returns the array; all uniform 300 m.
    assert out is not None
    assert (out == 300.0).all()


def test_w2_4_load_elevation_image_accepts_plan_bbox_kwarg(assemble_mod, tmp_path):
    """Plan bbox kwarg is the W2.4 routing hint; should not break the W2.2 path."""
    import numpy as np
    from PIL import Image
    arr = np.full((8, 8), 500, dtype=np.uint16)
    p = tmp_path / "dem.tif"
    Image.fromarray(arr, mode="I;16").save(p)
    # Pass plan_bbox → either rasterio path (if installed) or Pillow fallback.
    out = assemble_mod._load_elevation_image(
        p, 4, 4, plan_bbox=(0.0, 0.0, 1.0, 1.0),
    )
    assert out is not None
    assert out.shape == (4, 4)


def test_w2_2_terrain_emit_uses_real_elevation_when_path_set(assemble_mod, tmp_path):
    """`local_geotiff_path` on terrain layer → elevation comes from raster."""
    import numpy as np
    from PIL import Image
    # 8x8 single-band uint16, all elevation = 500m.
    arr = np.full((8, 8), 500, dtype=np.uint16)
    dem = tmp_path / "dem.tif"
    Image.fromarray(arr, mode="I;16").save(dem)

    scene_dir = tmp_path / "real-dem-scene"
    scene_dir.mkdir()
    (scene_dir / "scene.yaml").write_text(
        "adr: ADR-2605262500\nphase: W2\nsim_consumer: test\n"
        "world:\n"
        "  crs: EPSG:4326\n"
        "  bbox: [139.69, 35.65, 139.71, 35.67]\n"
        "  output_subdataset: x/\n"
        "  layers:\n"
        "    - kind: terrain\n"
        "      source_subdataset: geo/srtm/test\n"
        "      datasetPin_at: at://test/<rkey>\n"
        "      tier: A\n"
        "      mesh: {target_edge_m: 200.0}\n"   # ~10×12 grid
        f"      local_geotiff_path: {dem}\n",
        encoding="utf-8",
    )
    plan = assemble_mod.build_plan(scene_dir / "scene.yaml")
    layer = plan.layers[0]
    usda = assemble_mod._emit_terrain_usda(layer, plan, "T")
    # Source token must reflect real ingest.
    assert "pillow-elevation-w2.2" in usda
    assert "synth-cid-seeded" not in usda
    # All elevation values should be exactly 500 (mass-uniform DEM).
    assert ", 500.000)" in usda


def test_w2_2_terrain_falls_back_to_synth_when_path_missing(assemble_mod, tmp_path):
    scene_dir = tmp_path / "missing-dem-scene"
    scene_dir.mkdir()
    (scene_dir / "scene.yaml").write_text(
        "adr: ADR-2605262500\nphase: W2\nsim_consumer: test\n"
        "world:\n"
        "  crs: EPSG:4326\n"
        "  bbox: [139.69, 35.65, 139.71, 35.67]\n"
        "  output_subdataset: x/\n"
        "  layers:\n"
        "    - kind: terrain\n"
        "      source_subdataset: geo/srtm/test\n"
        "      datasetPin_at: at://test/<rkey>\n"
        "      tier: A\n"
        f"      local_geotiff_path: {tmp_path / 'no-such-dem.tif'}\n",
        encoding="utf-8",
    )
    plan = assemble_mod.build_plan(scene_dir / "scene.yaml")
    usda = assemble_mod._emit_terrain_usda(plan.layers[0], plan, "T")
    # Falls back to synth-cid-seeded (file doesn't exist).
    assert "synth-cid-seeded-w2.1" in usda


def test_w2_2_raster_overlay_stub_when_no_path(assemble_mod):
    """No `local_geotiff_path` → emit W2.0 stub Material (no texture binding)."""
    plan = assemble_mod.build_plan(_WADACHI_SCENE)
    layer = next(l for l in plan.layers if l.kind == "raster_overlay")
    usda = assemble_mod._emit_raster_overlay_usda(layer, plan, "M")
    assert 'def Material "M"' in usda
    assert "stub-w2.0-no-binding" in usda
    # No texture shader nodes in stub mode.
    assert "UsdUVTexture" not in usda


def test_w2_2_raster_overlay_real_texture_when_path_set(assemble_mod, tmp_path):
    """`local_geotiff_path` set → emit Material with UsdUVTexture binding."""
    scene_dir = tmp_path / "wadachi-with-overlay"
    scene_dir.mkdir()
    raster = tmp_path / "shibuya-rgb.png"
    _make_test_image(raster)
    (scene_dir / "scene.yaml").write_text(
        "adr: ADR-2605262500\nphase: W2\nsim_consumer: test\n"
        "world:\n"
        "  crs: EPSG:4326\n"
        "  bbox: [139.69, 35.65, 139.71, 35.67]\n"
        "  output_subdataset: x/\n"
        "  layers:\n"
        "    - kind: terrain\n"
        "      source_subdataset: geo/srtm/test\n"
        "      datasetPin_at: at://test/<rkey>\n"
        "      tier: A\n"
        "    - kind: raster_overlay\n"
        "      source_subdataset: geo/sentinel2/test\n"
        "      datasetPin_at: at://test/<rkey>\n"
        "      tier: A\n"
        f"      local_geotiff_path: {raster}\n",
        encoding="utf-8",
    )
    plan = assemble_mod.build_plan(scene_dir / "scene.yaml")
    layer = next(l for l in plan.layers if l.kind == "raster_overlay")
    usda = assemble_mod._emit_raster_overlay_usda(layer, plan, "M")
    assert "UsdUVTexture" in usda
    assert "UsdPrimvarReader_float2" in usda
    assert "@./textures/M.png@" in usda
    assert "pillow-sidecar-w2.2" in usda


def test_w2_2_write_raster_sidecar_creates_png(assemble_mod, tmp_path):
    """`_write_raster_sidecar` reads source + writes PNG sidecar."""
    src = tmp_path / "src.png"
    out_dir = tmp_path / "scene_out"
    _make_test_image(src)
    sidecar = assemble_mod._write_raster_sidecar(src, out_dir, "Layer1_raster_overlay")
    assert sidecar is not None
    assert sidecar.exists()
    assert sidecar.name == "Layer1_raster_overlay.png"
    assert sidecar.parent.name == "textures"


def test_w2_2_write_raster_sidecar_returns_none_when_src_missing(assemble_mod, tmp_path):
    sidecar = assemble_mod._write_raster_sidecar(
        tmp_path / "no-such-file.tif", tmp_path / "out", "M"
    )
    assert sidecar is None


def test_w2_2_emit_scene_writes_sidecars_and_records_in_manifest(assemble_mod, tmp_path):
    raster = tmp_path / "raster.png"
    _make_test_image(raster)
    scene_dir = tmp_path / "test-scene-with-overlay"
    scene_dir.mkdir()
    (scene_dir / "scene.yaml").write_text(
        "adr: ADR-2605262500\nphase: W2\nsim_consumer: test\n"
        "world:\n"
        "  crs: EPSG:4326\n"
        "  bbox: [139.69, 35.65, 139.71, 35.67]\n"
        "  output_subdataset: x/\n"
        "  layers:\n"
        "    - kind: terrain\n"
        "      source_subdataset: geo/srtm/x\n"
        "      datasetPin_at: at://x/<rkey>\n"
        "      tier: A\n"
        "    - kind: raster_overlay\n"
        "      source_subdataset: geo/sentinel2/x\n"
        "      datasetPin_at: at://x/<rkey>\n"
        "      tier: A\n"
        f"      local_geotiff_path: {raster}\n",
        encoding="utf-8",
    )
    plan = assemble_mod.build_plan(scene_dir / "scene.yaml")
    out_dir = tmp_path / "scene_out"
    manifest = assemble_mod.emit_scene(plan, out_dir)
    # The sidecar file must exist in the scene output dir.
    sidecar = out_dir / "textures" / "Layer1_raster_overlay.png"
    assert sidecar.exists()
    # The manifest records the sidecar copy operation.
    assert "texture_sidecars" in manifest
    recs = manifest["texture_sidecars"]
    assert len(recs) == 1
    assert recs[0]["prim_name"] == "Layer1_raster_overlay"
    assert recs[0]["sidecar"] == "textures/Layer1_raster_overlay.png"


# ─── W2.3 Charter rescan deepening (Parquet text-column extraction) ─


def test_charter_extract_parquet_text_sidecar_basic(assemble_mod, tmp_path):
    """`_extract_parquet_text_to_tempfile` writes per-column rows for string cols."""
    import pyarrow as pa
    import pyarrow.parquet as pq
    table = pa.table({
        "class": pa.array(["building", "warehouse", "residential"], type=pa.string()),
        "height": pa.array([10.0, 20.0, 8.0], type=pa.float64()),
        "name": pa.array(["A", "B", None], type=pa.string()),
    })
    parquet = tmp_path / "buildings.parquet"
    pq.write_table(table, parquet)
    out = tmp_path / "out"
    out.mkdir()
    sidecar = assemble_mod._extract_parquet_text_to_tempfile(parquet, out)
    assert sidecar is not None
    text = sidecar.read_text(encoding="utf-8")
    assert "class: building" in text
    assert "class: warehouse" in text
    assert "name: A" in text
    # height (float64) not included; None value skipped.
    assert "height" not in text
    assert "name: None" not in text


def test_charter_extract_returns_none_when_no_string_columns(assemble_mod, tmp_path):
    import pyarrow as pa
    import pyarrow.parquet as pq
    table = pa.table({
        "x": pa.array([1.0, 2.0], type=pa.float64()),
        "y": pa.array([3, 4], type=pa.int64()),
    })
    parquet = tmp_path / "no-strings.parquet"
    pq.write_table(table, parquet)
    sidecar = assemble_mod._extract_parquet_text_to_tempfile(parquet, tmp_path)
    assert sidecar is None


def test_charter_collect_scan_targets_includes_parquet_sidecars(assemble_mod, tmp_path):
    """`_collect_charter_scan_targets` adds Parquet text sidecars to scan list."""
    import pyarrow as pa
    import pyarrow.parquet as pq
    parquet = tmp_path / "data.parquet"
    pq.write_table(
        pa.table({"name": pa.array(["safe-building"], type=pa.string())}),
        parquet,
    )
    scene = tmp_path / "scene.yaml"
    scene.write_text("test scene")
    out = tmp_path / "out"
    out.mkdir()

    # Build a fake LayerPlan referencing the parquet.
    layer = assemble_mod.LayerPlan(
        index=0, kind="vector_buildings",
        source_subdataset="x", datasetPin_at="at://x/<rkey>",
        tier="A", resolved_cid="bafy0", dispatch_handler="kami-usd:test",
        extra={"local_parquet_path": str(parquet)},
    )
    paths, sidecars = assemble_mod._collect_charter_scan_targets(
        scene, [layer], [], out,
    )
    # scene.yaml + 1 sidecar
    assert len(paths) == 2
    assert paths[0] == scene
    assert len(sidecars) == 1
    assert sidecars[0].name == "charter-rescan-data.parquet.txt"
    assert sidecars[0].read_text().startswith("name: safe-building")


def test_charter_collect_skips_layers_without_parquet(assemble_mod, tmp_path):
    scene = tmp_path / "scene.yaml"
    scene.write_text("x")
    out = tmp_path / "out"
    out.mkdir()
    layer = assemble_mod.LayerPlan(
        index=0, kind="terrain",
        source_subdataset="x", datasetPin_at="at://x/<rkey>",
        tier="A", resolved_cid="bafy0", dispatch_handler="kami-usd:terrain",
        extra={"local_geotiff_path": "/tmp/no-parquet.tif"},  # image, not Parquet
    )
    paths, sidecars = assemble_mod._collect_charter_scan_targets(
        scene, [layer], [], out,
    )
    # Only scene.yaml; image path NOT scanned (vision-PII layer's job).
    assert paths == [scene]
    assert sidecars == []


# ─── W2.3 Charter rescan E2E — prohibited content catches ──────────


class _FakeCharterModule:
    """Stand-in for `e7m_dataset.charter` that the assemble script can import.

    Replaces the real wrapper around `kotodama.organism.sensors.charter_rider`
    with a controllable function. Used by tests to verify the assemble
    plumbing actually wires Parquet sidecars into scan_sample and that a
    `passed=False` verdict propagates as a RuntimeError.
    """

    def __init__(self, *, passed: bool, violations: list[dict] | None = None) -> None:
        self.passed = passed
        self.violations = violations or []
        self.calls: list[dict] = []   # records each scan_sample invocation

    def scan_sample(self, paths, *, kind, sample_rows=200):
        # Record what the caller passed so tests can assert on the call shape.
        path_strs = [str(p) for p in paths]
        text_samples: list[str] = []
        for p in paths:
            try:
                text_samples.append(_read_text(p))
            except Exception:
                text_samples.append("")
        self.calls.append({
            "paths": path_strs,
            "kind": kind,
            "sample_rows": sample_rows,
            "texts": text_samples,
        })
        return {
            "passed": self.passed,
            "at": "2026-05-27T00:00:00Z",
            "sampled": len(paths),
            "violations": self.violations,
            "note": "test-fake-scanner",
        }


def _read_text(p):
    from pathlib import Path as _Path
    return _Path(p).read_text(encoding="utf-8", errors="replace")


def test_charter_rescan_e2e_passes_when_parquet_clean(
    assemble_mod, monkeypatch, tmp_path,
):
    """Full integration: scene.yaml + safe Parquet → fake scanner passes →
    no RuntimeError; manifest records Parquet sidecar count."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    parquet = tmp_path / "safe.parquet"
    pq.write_table(
        pa.table({
            "class": pa.array(["building", "warehouse"], type=pa.string()),
            "name": pa.array(["A", "B"], type=pa.string()),
        }),
        parquet,
    )
    scene_dir = tmp_path / "clean-scene"
    scene_dir.mkdir()
    (scene_dir / "scene.yaml").write_text(
        "adr: ADR-2605262500\nphase: W2\nsim_consumer: test\n"
        "world:\n"
        "  crs: EPSG:4326\n"
        "  bbox: [139.69, 35.65, 139.71, 35.67]\n"
        "  output_subdataset: x/\n"
        "  layers:\n"
        "    - kind: terrain\n"
        "      source_subdataset: geo/srtm/test\n"
        "      datasetPin_at: at://test/<rkey>\n"
        "      tier: A\n"
        "    - kind: vector_buildings\n"
        "      source_subdataset: geo/overture/buildings/test\n"
        "      datasetPin_at: at://test/<rkey>\n"
        "      tier: A\n"
        f"      local_parquet_path: {parquet}\n",
        encoding="utf-8",
    )

    fake = _FakeCharterModule(passed=True)
    monkeypatch.setattr(assemble_mod, "_try_import_charter", lambda: fake)

    plan = assemble_mod.build_plan(scene_dir / "scene.yaml")
    assert plan.charter_attestations["scan_status"] == "passed-recipe-scan"
    assert plan.charter_attestations["scope"] == "scene-recipe-yaml+parquet-text"
    assert plan.charter_attestations["parquet_sidecar_count"] == 1
    assert plan.charter_attestations["scan_target_count"] == 2   # scene.yaml + 1 sidecar

    # The fake recorded one call; the Parquet text must be in the scanned content.
    assert len(fake.calls) == 1
    all_text = "\n".join(fake.calls[0]["texts"])
    assert "class: building" in all_text
    assert "name: A" in all_text


def test_charter_rescan_e2e_aborts_when_parquet_has_prohibited_content(
    assemble_mod, monkeypatch, tmp_path,
):
    """End-to-end §2 violation catch: Parquet row with prohibited keyword →
    fake scanner returns passed=False → build_plan raises RuntimeError.

    This proves the cycle 29 deepening actually closes the §2 catch loop —
    Parquet text content (not just scene.yaml) flows through scan_sample
    and a fail verdict propagates as an abort."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    parquet = tmp_path / "bad.parquet"
    pq.write_table(
        pa.table({
            "class": pa.array(["assault_rifle_carrier_truck"], type=pa.string()),
            "name": pa.array(["mil-vehicle-001"], type=pa.string()),
        }),
        parquet,
    )
    scene_dir = tmp_path / "bad-scene"
    scene_dir.mkdir()
    (scene_dir / "scene.yaml").write_text(
        "adr: ADR-2605262500\nphase: W2\nsim_consumer: test\n"
        "world:\n"
        "  crs: EPSG:4326\n"
        "  bbox: [139.69, 35.65, 139.71, 35.67]\n"
        "  output_subdataset: x/\n"
        "  layers:\n"
        "    - kind: terrain\n"
        "      source_subdataset: geo/srtm/test\n"
        "      datasetPin_at: at://test/<rkey>\n"
        "      tier: A\n"
        "    - kind: vector_buildings\n"
        "      source_subdataset: geo/overture/buildings/test\n"
        "      datasetPin_at: at://test/<rkey>\n"
        "      tier: A\n"
        f"      local_parquet_path: {parquet}\n",
        encoding="utf-8",
    )

    fake = _FakeCharterModule(
        passed=False,
        violations=[{
            "category": "2a",
            "label": "WEAPONS_AND_MILITARY",
            "match": "assault_rifle_carrier_truck",
        }],
    )
    monkeypatch.setattr(assemble_mod, "_try_import_charter", lambda: fake)

    with pytest.raises(RuntimeError, match="Charter Rider §2 scan FAILED"):
        assemble_mod.build_plan(scene_dir / "scene.yaml")

    # The fake was actually called with the Parquet sidecar content.
    assert len(fake.calls) == 1
    all_text = "\n".join(fake.calls[0]["texts"])
    assert "assault_rifle_carrier_truck" in all_text


def test_charter_rescan_e2e_no_parquet_only_scene_yaml(
    assemble_mod, monkeypatch, tmp_path,
):
    """When no layer has local_parquet_path, only scene.yaml is in scan list."""
    scene_dir = tmp_path / "no-parquet-scene"
    scene_dir.mkdir()
    (scene_dir / "scene.yaml").write_text(
        "adr: ADR-2605262500\nphase: W2\nsim_consumer: test\n"
        "world:\n"
        "  crs: EPSG:4326\n"
        "  bbox: [139.69, 35.65, 139.71, 35.67]\n"
        "  output_subdataset: x/\n"
        "  layers:\n"
        "    - kind: terrain\n"
        "      source_subdataset: geo/srtm/test\n"
        "      datasetPin_at: at://test/<rkey>\n"
        "      tier: A\n",
        encoding="utf-8",
    )
    fake = _FakeCharterModule(passed=True)
    monkeypatch.setattr(assemble_mod, "_try_import_charter", lambda: fake)
    plan = assemble_mod.build_plan(scene_dir / "scene.yaml")
    assert plan.charter_attestations["parquet_sidecar_count"] == 0
    assert plan.charter_attestations["scan_target_count"] == 1   # scene.yaml only
    assert len(fake.calls) == 1
    assert len(fake.calls[0]["paths"]) == 1


def test_charter_rescan_e2e_temp_sidecars_cleaned_up(
    assemble_mod, monkeypatch, tmp_path,
):
    """After successful build_plan, the temp sidecar directory should be removed."""
    import pyarrow as pa
    import pyarrow.parquet as pq
    parquet = tmp_path / "data.parquet"
    pq.write_table(
        pa.table({"name": pa.array(["safe-row"], type=pa.string())}),
        parquet,
    )
    scene_dir = tmp_path / "cleanup-scene"
    scene_dir.mkdir()
    (scene_dir / "scene.yaml").write_text(
        "adr: ADR-2605262500\nphase: W2\nsim_consumer: test\n"
        "world:\n"
        "  crs: EPSG:4326\n"
        "  bbox: [139.69, 35.65, 139.71, 35.67]\n"
        "  output_subdataset: x/\n"
        "  layers:\n"
        "    - kind: terrain\n"
        "      source_subdataset: geo/srtm/x\n"
        "      datasetPin_at: at://x/<rkey>\n"
        "      tier: A\n"
        "    - kind: vector_buildings\n"
        "      source_subdataset: geo/overture/x\n"
        "      datasetPin_at: at://x/<rkey>\n"
        "      tier: A\n"
        f"      local_parquet_path: {parquet}\n",
        encoding="utf-8",
    )
    fake = _FakeCharterModule(passed=True)
    monkeypatch.setattr(assemble_mod, "_try_import_charter", lambda: fake)

    import tempfile as _tempfile
    import glob
    # Snapshot the system temp dir before + after.
    before = set(glob.glob(str(_tempfile.gettempdir()) + "/e7m-charter-rescan-*"))
    plan = assemble_mod.build_plan(scene_dir / "scene.yaml")
    after = set(glob.glob(str(_tempfile.gettempdir()) + "/e7m-charter-rescan-*"))
    # No new temp dirs left behind.
    assert after - before == set()


def test_charter_collect_skips_missing_parquet(assemble_mod, tmp_path):
    """Non-existent local_parquet_path is silently skipped (no scan target)."""
    scene = tmp_path / "scene.yaml"
    scene.write_text("x")
    out = tmp_path / "out"
    out.mkdir()
    layer = assemble_mod.LayerPlan(
        index=0, kind="vector_buildings",
        source_subdataset="x", datasetPin_at="at://x/<rkey>",
        tier="A", resolved_cid="bafy0", dispatch_handler="kami-usd:test",
        extra={"local_parquet_path": "/tmp/does-not-exist.parquet"},
    )
    paths, sidecars = assemble_mod._collect_charter_scan_targets(
        scene, [layer], [], out,
    )
    assert paths == [scene]
    assert sidecars == []


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
