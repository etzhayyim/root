"""Tests for the geospatial fetchers landed by ADR-2605262500 W1.

Covers sentinel2.py / srtm.py / overture.py — the Tier-A fetchers used
by the wadachi R1 Shibuya 1km outdoor sim scene. Network access is
mocked via httpx.MockTransport so the suite runs offline in CI.
"""

from __future__ import annotations

import io
import json

import httpx
import pytest

from e7m_dataset.fetchers import (
    hf_3d_nc,
    mapillary,
    ms_buildings,
    openusd_samples,
    overture,
    sentinel2,
    srtm,
    usgs_3dep,
)
from e7m_dataset.vision_pii_filter import (
    DetectionBox,
    StubBackendConfig,
    StubVisionPiiBackend,
    VisionPiiBackendUnavailable,
    VisionPiiFilter,
)


# ─── SRTM (OpenTopography) ──────────────────────────────────────────


def test_srtm_parse_tile_id_n35e139_shibuya():
    """n35e139 covers 35-36°N × 139-140°E — the Tokyo Shibuya tile."""
    north, south, east, west = srtm._parse_tile_id("n35e139")
    assert (north, south, east, west) == (36.0, 35.0, 140.0, 139.0)
    # Shibuya bbox from scene.yaml is inside this tile.
    assert south <= 35.65 <= 35.67 <= north
    assert west <= 139.69 <= 139.71 <= east


def test_srtm_parse_tile_id_handles_south_west():
    """s12w077 covers 12-13°S × 76-77°W (Lima, Peru region)."""
    north, south, east, west = srtm._parse_tile_id("s12w077")
    assert north == -11.0
    assert south == -12.0
    assert east == -76.0
    assert west == -77.0


def test_srtm_parse_tile_id_rejects_garbage():
    with pytest.raises(ValueError, match="unrecognized SRTM tile id"):
        srtm._parse_tile_id("abc")           # too short
    with pytest.raises(ValueError, match="must start with"):
        srtm._parse_tile_id("x35e139")
    with pytest.raises(ValueError, match="missing 'e' or 'w'"):
        srtm._parse_tile_id("n35x139")
    with pytest.raises(ValueError, match="bad latitude digits"):
        srtm._parse_tile_id("nABe139")


def test_srtm_fetch_streams_geotiff(tmp_path):
    tif_bytes = b"II*\x00FAKE_GEOTIFF_FOR_TESTING" * 50
    captured: dict = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured["url"] = str(req.url)
        captured["params"] = dict(req.url.params)
        return httpx.Response(200, content=tif_bytes, headers={"content-type": "image/tiff"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = srtm.fetch(
            tmp_path,
            srtm.SrtmFetchOpts(tile_id="n35e139", client=client),
        )

    assert result.name == "srtm:n35e139"
    assert result.revision.startswith("srtm:SRTMGL1:n35e139:")
    assert result.file_count == 1
    assert result.size_bytes == len(tif_bytes)
    assert result.source["license"] == "public-domain-NASA"
    assert result.source["bbox"] == {"north": 36.0, "south": 35.0, "east": 140.0, "west": 139.0}
    # Verify the request carried the right OpenTopography params.
    assert captured["params"]["demtype"] == "SRTMGL1"
    assert captured["params"]["outputFormat"] == "GTiff"
    assert captured["params"]["south"] == "35.0"
    assert captured["params"]["north"] == "36.0"


# ─── Sentinel-2 (AWS Earth Search STAC) ─────────────────────────────


def test_sentinel2_stac_payload_for_tile_id():
    opts = sentinel2.Sentinel2FetchOpts(
        tile_id="T54SUE",
        datetime_range="2024-04-01/2024-05-31",
        cloud_cover_max=15.0,
    )
    payload = sentinel2._stac_search_payload(opts)
    assert payload["collections"] == [sentinel2.DEFAULT_COLLECTION]
    assert payload["query"]["grid:code"]["eq"] == "MGRS-54SUE"
    assert payload["query"]["eo:cloud_cover"]["lt"] == 15.0
    assert payload["datetime"] == "2024-04-01/2024-05-31"


def test_sentinel2_stac_payload_with_explicit_item_id():
    opts = sentinel2.Sentinel2FetchOpts(stac_item_id="S2A_T54SUE_20240501_0_L2A")
    payload = sentinel2._stac_search_payload(opts)
    assert payload["ids"] == ["S2A_T54SUE_20240501_0_L2A"]
    # Explicit-id mode should NOT carry a `query` filter.
    assert "query" not in payload


def test_sentinel2_stac_payload_requires_tile_id_or_item_id():
    with pytest.raises(ValueError, match="tile_id.+stac_item_id"):
        sentinel2._stac_search_payload(sentinel2.Sentinel2FetchOpts())


def test_sentinel2_select_item_picks_lowest_cloud():
    """STAC search returns sorted-asc, so we take features[0]."""
    features = [
        {"id": "low", "properties": {"eo:cloud_cover": 2.0}},
        {"id": "high", "properties": {"eo:cloud_cover": 18.0}},
    ]
    item = sentinel2._select_item(features, sentinel2.Sentinel2FetchOpts(tile_id="T54SUE"))
    assert item["id"] == "low"


def test_sentinel2_select_item_raises_on_empty():
    with pytest.raises(RuntimeError, match="no Sentinel-2 L2A scenes matched"):
        sentinel2._select_item([], sentinel2.Sentinel2FetchOpts(tile_id="T54SUE"))


def test_sentinel2_fetch_writes_stac_item_and_bands(tmp_path):
    fake_band_bytes = b"FAKE_COG_BYTES" * 100
    stac_item = {
        "id": "S2A_T54SUE_20240501_0_L2A",
        "properties": {"eo:cloud_cover": 3.7},
        "assets": {
            "B04": {"href": "https://example.invalid/B04.tif"},
            "B03": {"href": "https://example.invalid/B03.tif"},
            "B02": {"href": "https://example.invalid/B02.tif"},
        },
    }

    def handler(req: httpx.Request) -> httpx.Response:
        url = str(req.url)
        if req.method == "POST" and "search" in url:
            return httpx.Response(200, json={"features": [stac_item]})
        if url.endswith(".tif"):
            return httpx.Response(200, content=fake_band_bytes)
        return httpx.Response(404)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = sentinel2.fetch(
            tmp_path,
            sentinel2.Sentinel2FetchOpts(tile_id="T54SUE", client=client),
        )

    assert result.name == "sentinel2:S2A_T54SUE_20240501_0_L2A"
    assert result.revision == "stac:S2A_T54SUE_20240501_0_L2A"
    # 3 bands + 1 stac_item.json = 4 files.
    assert result.file_count == 4
    files = sorted(p.name for p in result.staging_path.iterdir())
    assert files == ["B02.tif", "B03.tif", "B04.tif", "stac_item.json"]
    persisted = json.loads((result.staging_path / "stac_item.json").read_text())
    assert persisted["id"] == "S2A_T54SUE_20240501_0_L2A"
    assert result.source["bands_fetched"] == ["B04", "B03", "B02"]
    assert result.source["cloud_cover_pct"] == 3.7
    assert result.source["license"] == "Copernicus-free-attribution"


# ─── Overture Maps Foundation ───────────────────────────────────────


def test_overture_validate_theme_type_known():
    overture._validate_theme_type("transportation", "segment")
    overture._validate_theme_type("buildings", "building")
    overture._validate_theme_type("base", "water")


def test_overture_validate_theme_type_rejects_unknown_theme():
    with pytest.raises(ValueError, match="unknown Overture theme"):
        overture._validate_theme_type("not-a-theme", "segment")


def test_overture_validate_theme_type_rejects_unknown_type():
    with pytest.raises(ValueError, match="unknown Overture type 'truck'"):
        overture._validate_theme_type("transportation", "truck")


def test_overture_known_themes_cover_adr_w1():
    """ADR-2605262500 §2 W1 needs transportation/segment + buildings/building."""
    assert "segment" in overture.KNOWN_THEME_TYPES["transportation"]
    assert "building" in overture.KNOWN_THEME_TYPES["buildings"]


def test_overture_fetch_first_shard_lists_and_streams(tmp_path):
    fake_parquet = b"PAR1FAKE_PARQUET" * 200
    list_xml = (
        "<?xml version='1.0'?>"
        "<ListBucketResult>"
        "<Contents><Key>release/2024-12-12.0/theme=transportation/"
        "type=segment/part-00000-deadbeef.parquet</Key></Contents>"
        "</ListBucketResult>"
    )

    def handler(req: httpx.Request) -> httpx.Response:
        url = str(req.url)
        if "list-type=2" in url:
            return httpx.Response(200, text=list_xml)
        if url.endswith(".parquet"):
            return httpx.Response(200, content=fake_parquet)
        return httpx.Response(404)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = overture.fetch(
            tmp_path,
            overture.OvertureFetchOpts(
                release="2024-12-12.0",
                theme="transportation",
                type_name="segment",
                client=client,
            ),
        )

    assert result.name == "overture:transportation:segment"
    assert result.revision == "overture:2024-12-12.0"
    assert result.file_count == 1
    assert result.size_bytes == len(fake_parquet)
    assert result.source["shard"] == "part-00000-deadbeef.parquet"
    assert result.source["license"] == "CDLA-Permissive-2.0"


def test_overture_fetch_rejects_unknown_theme(tmp_path):
    with pytest.raises(ValueError, match="unknown Overture theme"):
        overture.fetch(
            tmp_path,
            overture.OvertureFetchOpts(
                release="2024-12-12.0", theme="bogus", type_name="x"
            ),
        )


# ─── MS Global Building Footprints (W2 deliverable) ─────────────────


def _make_ms_index_csv() -> str:
    return (
        "Location,QuadKey,Url,Size\n"
        "Japan,133021133,"
        "https://minedbuildings.blob.core.windows.net/global-buildings/"
        "2024-04-04/global/Japan/quad_133021133.geojsonl.gz,12345\n"
        "Japan,133021332,"
        "https://minedbuildings.blob.core.windows.net/global-buildings/"
        "2024-04-04/global/Japan/quad_133021332.geojsonl.gz,9876\n"
        "Germany,120023213,"
        "https://minedbuildings.blob.core.windows.net/global-buildings/"
        "2024-04-04/global/Germany/quad_120023213.geojsonl.gz,5678\n"
    )


def test_ms_buildings_parse_index_csv_basic():
    rows = ms_buildings._parse_index_csv(_make_ms_index_csv())
    assert len(rows) == 3
    assert rows[0]["Location"] == "Japan"
    assert rows[0]["QuadKey"] == "133021133"
    assert "Japan" in rows[0]["Url"]


def test_ms_buildings_select_by_country():
    rows = ms_buildings._parse_index_csv(_make_ms_index_csv())
    row = ms_buildings._select_index_row(
        rows, ms_buildings.MsBuildingsFetchOpts(country="japan")
    )
    # First Japan row wins (deterministic).
    assert row["QuadKey"] == "133021133"


def test_ms_buildings_select_by_explicit_quadkey():
    rows = ms_buildings._parse_index_csv(_make_ms_index_csv())
    row = ms_buildings._select_index_row(
        rows, ms_buildings.MsBuildingsFetchOpts(quadkey="133021332")
    )
    assert row["Location"] == "Japan"
    assert row["QuadKey"] == "133021332"


def test_ms_buildings_select_rejects_unknown_country():
    rows = ms_buildings._parse_index_csv(_make_ms_index_csv())
    with pytest.raises(RuntimeError, match="no Location matching"):
        ms_buildings._select_index_row(
            rows, ms_buildings.MsBuildingsFetchOpts(country="atlantis")
        )


def test_ms_buildings_select_requires_country_or_quadkey():
    rows = ms_buildings._parse_index_csv(_make_ms_index_csv())
    with pytest.raises(ValueError, match="`country`.+`quadkey`"):
        ms_buildings._select_index_row(rows, ms_buildings.MsBuildingsFetchOpts())


def test_ms_buildings_fetch_streams_geojsonl(tmp_path):
    geojsonl = b'{"type":"Feature","geometry":{"type":"Polygon"}}\n' * 50

    def handler(req: httpx.Request) -> httpx.Response:
        url = str(req.url)
        if url.endswith("dataset-links.csv"):
            return httpx.Response(200, text=_make_ms_index_csv())
        if url.endswith(".geojsonl.gz"):
            return httpx.Response(200, content=geojsonl)
        return httpx.Response(404)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = ms_buildings.fetch(
            tmp_path,
            ms_buildings.MsBuildingsFetchOpts(country="Japan", client=client),
        )

    assert result.name == "ms-buildings:Japan:133021133"
    assert result.revision.startswith("ms-buildings:133021133:")
    assert result.source["license"] == "ODbL-1.0"
    assert result.source["quadkey"] == "133021133"
    # geojsonl + index_row.json
    assert result.file_count == 2


# ─── USGS 3DEP (W2 deliverable) ─────────────────────────────────────


def test_usgs_3dep_url_build():
    opts = usgs_3dep.Usgs3depFetchOpts(
        project="CA_NorCal_3DEP_2019_A19",
        tile_name="USGS_1m_10_x40y455_CA",
    )
    url = usgs_3dep._build_asset_url(opts)
    assert url == (
        "https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/1m/Projects/"
        "CA_NorCal_3DEP_2019_A19/TIFF/USGS_1m_10_x40y455_CA.tif"
    )


def test_usgs_3dep_requires_project_and_tile():
    with pytest.raises(ValueError, match="requires both"):
        usgs_3dep.fetch(
            __import__("pathlib").Path("/tmp"),
            usgs_3dep.Usgs3depFetchOpts(project="", tile_name=""),
        )


# ─── OpenUSD samples (Tier-A reference scenes) ──────────────────────


# ─── HF 3D NC (Tier-C, G13 fleet-internal) ──────────────────────────


def test_hf_3d_nc_resolve_repo_known_slug():
    owner, repo, slug, note = hf_3d_nc._resolve_repo(
        hf_3d_nc.Hf3dNcFetchOpts(slug="objaverse-xl-nc-cars")
    )
    assert owner == "allenai"
    assert repo == "objaverse-xl"
    assert slug == "objaverse-xl-nc-cars"
    assert "Passenger-car-set" in note or "NC" in note


def test_hf_3d_nc_resolve_repo_rejects_unknown_slug():
    with pytest.raises(ValueError, match="unknown HF 3D NC slug"):
        hf_3d_nc._resolve_repo(hf_3d_nc.Hf3dNcFetchOpts(slug="random-not-in-list"))


def test_hf_3d_nc_resolve_explicit_requires_acknowledgement():
    """G13 license-on-operator: explicit owner/repo without acknowledgement is fail-closed."""
    with pytest.raises(ValueError, match="explicit_nc_acknowledged"):
        hf_3d_nc._resolve_repo(
            hf_3d_nc.Hf3dNcFetchOpts(
                explicit_owner="someone",
                explicit_repo="some-3d-repo",
                explicit_nc_acknowledged=False,
            )
        )


def test_hf_3d_nc_resolve_explicit_with_acknowledgement_passes():
    owner, repo, slug, note = hf_3d_nc._resolve_repo(
        hf_3d_nc.Hf3dNcFetchOpts(
            explicit_owner="someone",
            explicit_repo="some-3d-repo",
            explicit_nc_acknowledged=True,
        )
    )
    assert owner == "someone"
    assert repo == "some-3d-repo"
    assert slug == "someone-some-3d-repo"
    assert "operator-supplied" in note


def test_hf_3d_nc_resolve_repo_requires_slug_or_explicit():
    with pytest.raises(ValueError, match="either .slug. .from KNOWN_NC_REPOS"):
        hf_3d_nc._resolve_repo(hf_3d_nc.Hf3dNcFetchOpts())


def test_hf_3d_nc_default_globs_lock_to_3d_extensions():
    """G13 hardening: arbitrary HF files are filtered to 3D-asset extensions only."""
    globs = hf_3d_nc.DEFAULT_3D_ASSET_GLOBS
    assert "*.glb" in globs
    assert "*.usd" in globs
    assert "*.usdz" in globs
    # No text / image / md / pickle should be included by default.
    assert all(not g.endswith(suffix) for g in globs
               for suffix in (".md", ".txt", ".json", ".png", ".jpg", ".pkl"))


def test_openusd_resolve_url_known_slug():
    url, slug = openusd_samples._resolve_url(
        openusd_samples.OpenUsdSamplesFetchOpts(slug="kitchen-set")
    )
    assert url == openusd_samples.KNOWN_SAMPLES["kitchen-set"]
    assert slug == "kitchen-set"


def test_openusd_resolve_url_explicit_overrides_allowlist():
    url, slug = openusd_samples._resolve_url(
        openusd_samples.OpenUsdSamplesFetchOpts(
            explicit_url="https://example.invalid/custom_scene.zip"
        )
    )
    assert url == "https://example.invalid/custom_scene.zip"
    assert slug == "custom_scene"


def test_openusd_resolve_url_rejects_unknown_slug():
    with pytest.raises(ValueError, match="unknown OpenUSD sample slug"):
        openusd_samples._resolve_url(
            openusd_samples.OpenUsdSamplesFetchOpts(slug="not-a-real-sample")
        )


def test_openusd_resolve_url_requires_slug_or_url():
    with pytest.raises(ValueError, match="`slug`.+`explicit_url`"):
        openusd_samples._resolve_url(openusd_samples.OpenUsdSamplesFetchOpts())


def test_openusd_fetch_streams_archive_and_computes_sha256(tmp_path):
    archive_bytes = b"PK\x03\x04FAKE_ZIP_BYTES" * 200
    import hashlib
    expected_sha = hashlib.sha256(archive_bytes).hexdigest()

    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=archive_bytes)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = openusd_samples.fetch(
            tmp_path,
            openusd_samples.OpenUsdSamplesFetchOpts(slug="kitchen-set", client=client),
        )

    assert result.name == "openusd-samples:kitchen-set"
    assert result.revision == f"sha256:{expected_sha}"
    assert result.file_count == 1
    assert result.size_bytes == len(archive_bytes)
    assert result.source["license"] == "Apache-2.0"
    assert result.source["slug"] == "kitchen-set"
    assert result.source["explicit_url"] is False


# ─── Mapillary (Tier-C, G13 / G2 vision PII filter required) ────────


def _tiny_jpeg() -> bytes:
    """Make a small 32x24 RGB JPEG for mapillary fetch smoke."""
    from PIL import Image
    import io as _io
    img = Image.new("RGB", (32, 24), color=(60, 80, 100))
    buf = _io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_mapillary_refuses_without_vision_pii_filter(tmp_path):
    """G2 enforcement at the fetcher boundary."""
    with pytest.raises(VisionPiiBackendUnavailable, match="vision_pii_filter"):
        mapillary.fetch(
            tmp_path,
            mapillary.MapillaryFetchOpts(
                bbox=(139.69, 35.65, 139.71, 35.67),
                token="fake-token-for-test",
                vision_pii_filter=None,
            ),
        )


def test_mapillary_fetch_with_stub_pii_redacts_and_pins_originals(tmp_path):
    """End-to-end smoke: stub PII filter + 2 fake images → 1 redacted + 1 rejected."""
    img_bytes = _tiny_jpeg()
    list_resp = {
        "data": [
            {"id": "img_001_safe", "captured_at": 1700000000, "thumb_2048_url": "https://example.invalid/img1.jpg"},
            {"id": "img_002_child", "captured_at": 1700000100, "thumb_2048_url": "https://example.invalid/img2.jpg"},
        ]
    }

    def handler(req: httpx.Request) -> httpx.Response:
        url = str(req.url)
        if "graph.mapillary.com/images" in url:
            return httpx.Response(200, json=list_resp)
        if url.endswith(".jpg"):
            return httpx.Response(200, content=img_bytes)
        return httpx.Response(404)

    # Stub backend will report a child face for img_002_child by mutating
    # config mid-fetch via a side-effect helper.
    class _SwitchingBackend:
        name = "stub-allow"

        def __init__(self):
            self._call_idx = 0

        def detect_faces(self, b):
            return [DetectionBox(x=4, y=4, w=8, h=8, score=0.9, label="face")]

        def detect_plates(self, b):
            return []

        def estimate_child_face_count(self, b, faces):
            self._call_idx += 1
            # The 1st detected image is adult; the 2nd has a child.
            return 1 if self._call_idx == 2 else 0

    vpf = VisionPiiFilter(backend=_SwitchingBackend(), allow_stub=True)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = mapillary.fetch(
            tmp_path,
            mapillary.MapillaryFetchOpts(
                bbox=(139.69, 35.65, 139.71, 35.67),
                token="fake-token-for-test",
                vision_pii_filter=vpf,
                client=client,
            ),
        )

    assert result.name.startswith("mapillary:")
    assert result.source["license"] == "CC-BY-SA-4.0"
    assert result.source["tier"] == "C"
    assert result.source["g13_nc_infix_required_in_artifacts"] is True
    assert result.source["n_fetched"] == 1
    assert result.source["n_rejected_for_child"] == 1
    # The redacted view exists for the safe image, NOT for the rejected one.
    redacted_imgs = sorted(p.name for p in (result.staging_path / "images").iterdir())
    assert redacted_imgs == ["img_001_safe.jpg"]
    # Both originals are preserved in annex (Council-attestation-gated unlock per §5).
    annex_imgs = sorted(p.name for p in (result.staging_path / "annex").iterdir())
    assert annex_imgs == ["img_001_safe.jpg", "img_002_child.jpg"]
    # Detection records for both; rejection record only for the child case.
    det_records = sorted(p.name for p in (result.staging_path / "detections").iterdir())
    assert det_records == ["img_001_safe.json", "img_002_child.json"]
    rej_records = sorted(p.name for p in (result.staging_path / "rejected").iterdir())
    assert rej_records == ["img_002_child.json"]


def test_mapillary_bbox_slug_stable():
    s1 = mapillary._bbox_slug((139.69, 35.65, 139.71, 35.67))
    s2 = mapillary._bbox_slug((139.69, 35.65, 139.71, 35.67))
    assert s1 == s2
    assert "139" in s1 and "35" in s1


def test_mapillary_max_images_capped():
    assert mapillary._cap_image_count(50) == 50
    assert mapillary._cap_image_count(mapillary.ABSOLUTE_MAX_IMAGES + 9999) == mapillary.ABSOLUTE_MAX_IMAGES
    with pytest.raises(ValueError):
        mapillary._cap_image_count(0)


def test_mapillary_requires_token(tmp_path, monkeypatch):
    monkeypatch.delenv("MAPILLARY_TOKEN", raising=False)
    monkeypatch.delenv("ETZ_MAPILLARY_TOKEN", raising=False)
    vpf = VisionPiiFilter(backend=StubVisionPiiBackend(), allow_stub=True)
    with pytest.raises(ValueError, match="Mapillary token required"):
        mapillary.fetch(
            tmp_path,
            mapillary.MapillaryFetchOpts(
                bbox=(0, 0, 1, 1),
                vision_pii_filter=vpf,
            ),
        )


def test_usgs_3dep_fetch_streams_tif(tmp_path):
    tif_bytes = b"II*\x00FAKE_USGS_GEOTIFF" * 30

    def handler(req: httpx.Request) -> httpx.Response:
        if str(req.url).endswith(".tif"):
            return httpx.Response(200, content=tif_bytes)
        return httpx.Response(404)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = usgs_3dep.fetch(
            tmp_path,
            usgs_3dep.Usgs3depFetchOpts(
                project="CA_NorCal_3DEP_2019_A19",
                tile_name="USGS_1m_10_x40y455_CA",
                client=client,
            ),
        )

    assert result.name == "usgs-3dep:CA_NorCal_3DEP_2019_A19:USGS_1m_10_x40y455_CA"
    assert result.revision.startswith("usgs-3dep:CA_NorCal_3DEP_2019_A19:USGS_1m_10_x40y455_CA:")
    assert result.file_count == 1
    assert result.size_bytes == len(tif_bytes)
    assert result.source["license"] == "public-domain-USGS"
