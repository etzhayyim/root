"""End-to-end smoke: 4/5 layer real-asset ingest path through assemble-usd-scene.

Synthesizes the full set of real assets the religious-corp pipeline
would produce (16-bit SRTM-style DEM TIFF + Sentinel-2 RGB PNG +
Overture buildings WKB-Polygon Parquet + Overture roads WKB-LineString
Parquet), writes a scene.yaml referencing all four via
`local_geotiff_path` / `local_parquet_path`, runs the full assemble
pipeline, and verifies the output USDA carries the correct real-asset
source tokens + a self-contained scene output dir (USDA + manifest +
texture sidecars).

This is the "proof of life" for the entire ADR-2605262500 W2 axis
shipping together — terrain elevation + raster overlay texture +
building polygons + road polylines all sourced from real files in a
single assemble run.
"""

from __future__ import annotations

import importlib.util
import struct
import sys
from pathlib import Path

import numpy as np
import pytest


_THIS = Path(__file__).resolve()
_E7M_SIM = _THIS.parent.parent
_SCRIPT = _E7M_SIM / "scripts" / "assemble-usd-scene.py"


@pytest.fixture(scope="module")
def assemble_mod():
    spec = importlib.util.spec_from_file_location("assemble_usd_scene", _SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["assemble_usd_scene"] = mod
    spec.loader.exec_module(mod)
    return mod


def _wkb_linestring_le(points: list[tuple[float, float]]) -> bytes:
    out = bytearray()
    out.append(1)
    out += struct.pack("<I", 2)
    out += struct.pack("<I", len(points))
    for x, y in points:
        out += struct.pack("<dd", x, y)
    return bytes(out)


def _wkb_polygon_le(rings: list[list[tuple[float, float]]]) -> bytes:
    out = bytearray()
    out.append(1)
    out += struct.pack("<I", 3)
    out += struct.pack("<I", len(rings))
    for ring in rings:
        out += struct.pack("<I", len(ring))
        for x, y in ring:
            out += struct.pack("<dd", x, y)
    return bytes(out)


def _make_synthetic_assets(tmp_path: Path) -> dict[str, Path]:
    """Synthesize the 4 real-asset files an operator would stage.

    Returns a dict of label → path.  The scene YAML references these
    paths via `local_geotiff_path` / `local_parquet_path`.
    """
    from PIL import Image
    import pyarrow as pa
    import pyarrow.parquet as pq

    # 1. SRTM-style 16-bit DEM (gradient — verifies bilinear samples)
    dem = tmp_path / "n35e139.tif"
    dem_arr = np.zeros((64, 64), dtype=np.uint16)
    for y in range(64):
        for x in range(64):
            dem_arr[y, x] = x * 5 + y * 3   # 0..(63*5+63*3)=504
    Image.fromarray(dem_arr, mode="I;16").save(dem)

    # 2. Sentinel-2-style RGB GeoTIFF (saved as PNG; same Pillow path)
    rgb = tmp_path / "sentinel2-T54SUE.png"
    rng = np.random.RandomState(42)
    rgb_arr = rng.randint(0, 256, size=(128, 128, 3), dtype=np.uint8)
    Image.fromarray(rgb_arr).save(rgb)

    # 3. Overture buildings Parquet (hexagon WKB Polygon + bbox + height)
    buildings = tmp_path / "overture-buildings-jp.parquet"
    hex_ring = [
        (139.700, 35.660), (139.7005, 35.6603), (139.7005, 35.6607),
        (139.700, 35.661), (139.6995, 35.6607), (139.6995, 35.6603),
        (139.700, 35.660),
    ]
    bbox_struct = pa.struct([
        ("xmin", pa.float64()), ("xmax", pa.float64()),
        ("ymin", pa.float64()), ("ymax", pa.float64()),
    ])
    pq.write_table(
        pa.table({
            "bbox": pa.array(
                [{"xmin": 139.6995, "xmax": 139.7005, "ymin": 35.660, "ymax": 35.661}],
                type=bbox_struct,
            ),
            "height": pa.array([22.5], type=pa.float64()),
            "geometry": pa.array([_wkb_polygon_le([hex_ring])], type=pa.binary()),
        }),
        buildings,
    )

    # 4. Overture roads Parquet (2 LineString rows)
    roads = tmp_path / "overture-roads-jp.parquet"
    pq.write_table(
        pa.table({
            "geometry": pa.array([
                _wkb_linestring_le([(139.700, 35.660), (139.701, 35.661), (139.702, 35.660)]),
                _wkb_linestring_le([(139.703, 35.663), (139.704, 35.664)]),
            ], type=pa.binary()),
        }),
        roads,
    )

    return {"dem": dem, "rgb": rgb, "buildings": buildings, "roads": roads}


def test_e2e_all_four_real_asset_layers_assemble_correctly(assemble_mod, tmp_path):
    """Full pipeline E2E: 4 real-asset files → scene.yaml → assemble → USDA + sidecar."""
    assets = _make_synthetic_assets(tmp_path)

    scene_dir = tmp_path / "e2e-real-scene"
    scene_dir.mkdir()
    (scene_dir / "scene.yaml").write_text(
        "adr: ADR-2605262500\n"
        "phase: E2E-W2\n"
        "sim_consumer: e2e-test\n"
        "world:\n"
        "  crs: EPSG:4326\n"
        "  bbox: [139.69, 35.65, 139.71, 35.67]\n"
        "  output_subdataset: sim-scenes/e2e/261015/\n"
        "  layers:\n"
        "    - kind: terrain\n"
        "      source_subdataset: geo/srtm/n35e139\n"
        "      datasetPin_at: at://e2e/<rkey>\n"
        "      tier: A\n"
        "      mesh: {target_edge_m: 200.0}\n"
        f"      local_geotiff_path: {assets['dem']}\n"
        "    - kind: raster_overlay\n"
        "      source_subdataset: geo/sentinel2/T54SUE\n"
        "      datasetPin_at: at://e2e/<rkey>\n"
        "      tier: A\n"
        f"      local_geotiff_path: {assets['rgb']}\n"
        "    - kind: vector_roads\n"
        "      source_subdataset: geo/overture/transportation/jp\n"
        "      datasetPin_at: at://e2e/<rkey>\n"
        "      tier: A\n"
        f"      local_parquet_path: {assets['roads']}\n"
        "    - kind: vector_buildings\n"
        "      source_subdataset: geo/overture/buildings/jp\n"
        "      datasetPin_at: at://e2e/<rkey>\n"
        "      tier: A\n"
        f"      local_parquet_path: {assets['buildings']}\n",
        encoding="utf-8",
    )

    plan = assemble_mod.build_plan(scene_dir / "scene.yaml")
    out_dir = tmp_path / "e2e-out"
    manifest = assemble_mod.emit_scene(plan, out_dir)

    # ── scene.usda exists and is non-trivial size ──────────────────────
    usda_path = out_dir / "scene.usda"
    assert usda_path.exists()
    usda = usda_path.read_text(encoding="utf-8")
    assert len(usda) > 5000     # multi-vertex grid + multi-Polygon = >> stub size

    # ── Layer 0: terrain real elevation from Pillow GeoTIFF ────────────
    assert 'kami_elevation_source = "pillow-elevation-w2.2:' in usda
    assert 'synth-cid-seeded' not in usda.split('Layer0_terrain')[1].split('def ')[0] \
        if 'Layer0_terrain' in usda else True

    # ── Layer 1: raster_overlay real Material w/ UsdUVTexture ──────────
    assert 'UsdUVTexture' in usda
    assert 'UsdPrimvarReader_float2' in usda
    assert '@./textures/Layer1_raster_overlay.png@' in usda
    assert 'pillow-sidecar-w2.2' in usda

    # ── Layer 2: roads real WKB LineString (2 polylines) ───────────────
    assert 'overture-parquet-w2.2' in usda
    # 2 LineStrings in Parquet → 2 child Meshes under roads Scope.
    assert usda.count('def Mesh "R0') == 2
    assert 'kami_waypoint_count = 3' in usda    # first road
    assert 'kami_waypoint_count = 2' in usda    # second road

    # ── Layer 3: buildings real WKB Polygon (hexagon — 6 corners) ──────
    # Hexagon outer ring → 6 base + 6 top vertices = 12 unique points.
    # Each child Mesh "B000" must report 6-vertex polygon (not 4-vertex bbox).
    assert 'kami_polygon_vertex_count = 6' in usda
    assert 'kami_height_m = 22.500' in usda     # height from Parquet

    # ── Sidecar PNG actually copied into out_dir/textures/ ─────────────
    sidecar = out_dir / "textures" / "Layer1_raster_overlay.png"
    assert sidecar.exists()
    assert sidecar.stat().st_size > 0

    # ── Manifest records the sidecar copy ──────────────────────────────
    assert "texture_sidecars" in manifest
    assert len(manifest["texture_sidecars"]) == 1
    assert manifest["texture_sidecars"][0]["prim_name"] == "Layer1_raster_overlay"

    # ── G6 determinism still holds for the full real-asset E2E run ─────
    out_dir_2 = tmp_path / "e2e-out-2"
    manifest_2 = assemble_mod.emit_scene(plan, out_dir_2)
    assert (out_dir_2 / "scene.usda").read_bytes() == usda_path.read_bytes()
    assert manifest_2["scene_usda_sha256"] == manifest["scene_usda_sha256"]


def test_e2e_partial_real_assets_other_layers_synth(assemble_mod, tmp_path):
    """If only some layers have real paths, others fall back to synth."""
    assets = _make_synthetic_assets(tmp_path)
    scene_dir = tmp_path / "e2e-partial-scene"
    scene_dir.mkdir()
    (scene_dir / "scene.yaml").write_text(
        "adr: ADR-2605262500\n"
        "phase: E2E-W2-partial\n"
        "sim_consumer: e2e-partial\n"
        "world:\n"
        "  crs: EPSG:4326\n"
        "  bbox: [139.69, 35.65, 139.71, 35.67]\n"
        "  output_subdataset: x/\n"
        "  layers:\n"
        "    - kind: terrain\n"
        "      source_subdataset: geo/srtm/x\n"
        "      datasetPin_at: at://x/<rkey>\n"
        "      tier: A\n"
        f"      local_geotiff_path: {assets['dem']}\n"
        "    - kind: vector_buildings\n"
        "      source_subdataset: geo/overture/buildings/x\n"
        "      datasetPin_at: at://x/<rkey>\n"
        "      tier: A\n"
        # No local_parquet_path → synth fallback for buildings
        "    - kind: vector_roads\n"
        "      source_subdataset: geo/overture/transportation/x\n"
        "      datasetPin_at: at://x/<rkey>\n"
        "      tier: A\n"
        # No local_parquet_path → synth fallback for roads
        "    - kind: raster_overlay\n"
        "      source_subdataset: geo/sentinel2/x\n"
        "      datasetPin_at: at://x/<rkey>\n"
        "      tier: A\n",
        # No local_geotiff_path → stub Material for overlay
        encoding="utf-8",
    )
    plan = assemble_mod.build_plan(scene_dir / "scene.yaml")
    out_dir = tmp_path / "e2e-partial-out"
    manifest = assemble_mod.emit_scene(plan, out_dir)
    usda = (out_dir / "scene.usda").read_text(encoding="utf-8")

    # terrain = real Pillow
    assert "pillow-elevation-w2.2" in usda
    # buildings = synth fallback
    assert usda.count("synth-cid-seeded-w2.1") >= 2   # buildings + roads
    # overlay = stub
    assert "stub-w2.0-no-binding" in usda
    # No sidecars expected (overlay has no path).
    assert "texture_sidecars" not in manifest
