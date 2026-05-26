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


# ─── module loading ─────────────────────────────────────────────────

_THIS = Path(__file__).resolve()
_E7M_SIM = _THIS.parent.parent
_SCRIPT = _E7M_SIM / "scripts" / "assemble-usd-scene.py"
_WADACHI_SCENE = _E7M_SIM / "scenes" / "wadachi-r1-shibuya-1km" / "scene.yaml"
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


def test_scene_schema_file_is_valid_json():
    """Sanity-check the schema is parseable JSON regardless of jsonschema availability."""
    body = json.loads(_SCHEMA.read_text(encoding="utf-8"))
    assert body.get("$schema", "").endswith("/2020-12/schema")
    assert "properties" in body
    assert "world" in body["properties"]
    assert "worldLayer" in body["$defs"]
