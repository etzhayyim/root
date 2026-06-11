"""maps3d.colmapTile + maps3d.simplifyAndExport — real CPU pipeline.

Phase 2 production handler. Wraps the seven-step COLMAP CPU pipeline
(`_colmap.py`), Open3D quadric-decimation (`_mesh.py`), and B2 upload
(`_b2.py`) into two LangServer handlers that match the lexicon
contracts in `00-contracts/lexicons/com/etzhayyim/apps/maps3d/`.

Operational notes:
  - SCRATCH_DIR (default /scratch) holds the per-tile work tree;
    cleaned between tiles. Sized via emptyDir 8 GiB in colmap-worker.yaml.
  - Each handler enforces an end-to-end timeout that is **shorter** than
    the BPMN boundary (60 min) so the subprocess tree gets SIGKILL'd
    before AgentGateway retries the job and another worker picks it up.
  - On any failure the handler returns `ok=false` plus an error_code
    from the colmapTile.json taxonomy. The BPMN exclusive gateway
    routes failures to `replanReconstruction`.
"""

from __future__ import annotations

import asyncio
import os
import shutil
import time
from pathlib import Path
from typing import Any

import httpx

from ._b2 import B2Client
from ._colmap import (
    ERR_TIMEOUT,
    ERR_UNKNOWN,
    PipelineResult,
    cleanup_workdir,
    run_pipeline,
)
from ._common import log, make_worker, run_forever, task

SCRATCH_DIR = Path(os.environ.get("SCRATCH_DIR", "/scratch"))
COLMAP_BIN = os.environ.get("COLMAP_BIN", "/usr/bin/colmap")
B2_BUCKET = os.environ.get("B2_BUCKET", "etzhayyim-nats")
# colmapTile budget — keep below the BPMN boundary timer (60 min).
COLMAP_BUDGET_S = int(os.environ.get("MAPS3D_COLMAP_BUDGET_S", "3300"))  # 55 min
SIMPLIFY_BUDGET_S = int(os.environ.get("MAPS3D_SIMPLIFY_BUDGET_S", "300"))  # 5 min
DOWNLOAD_TIMEOUT_S = int(os.environ.get("MAPS3D_DOWNLOAD_TIMEOUT_S", "300"))  # 5 min for all images

_b2: B2Client | None = None


def _b2_client() -> B2Client:
    global _b2
    if _b2 is None:
        _b2 = B2Client(bucket=B2_BUCKET)
    return _b2


# ─── Mapillary URL → /scratch/images ────────────────────────────────


async def _download_images(
    urls: list[str], target_dir: Path, total_timeout_s: int
) -> int:
    """Download all images into `target_dir`, naming them by index so
    COLMAP picks them up alphabetically. Returns the count successfully
    saved. Skips any URL that fails individually — COLMAP works fine on
    a partial set if enough cameras remain."""
    target_dir.mkdir(parents=True, exist_ok=True)
    saved = 0
    deadline = time.perf_counter() + total_timeout_s
    timeout = httpx.Timeout(connect=10.0, read=30.0, write=30.0, pool=30.0)
    async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
        for i, url in enumerate(urls):
            if time.perf_counter() >= deadline:
                log.warning("download deadline hit at %d/%d", saved, len(urls))
                break
            try:
                r = await client.get(url)
                r.raise_for_status()
                # Suffix from URL or default to .jpg.
                suffix = Path(url.split("?", 1)[0]).suffix or ".jpg"
                if suffix.lower() not in {".jpg", ".jpeg", ".png"}:
                    suffix = ".jpg"
                out = target_dir / f"{i:04d}{suffix}"
                out.write_bytes(r.content)
                saved += 1
            except (httpx.HTTPError, OSError) as exc:
                log.warning("download skipped %s: %s", url, exc)
    log.info("downloaded %d/%d images to %s", saved, len(urls), target_dir)
    return saved


def _normalize_image_urls(image_urls: Any) -> list[str]:
    """Accept either a list of plain URL strings or a list of Mapillary
    candidate dicts (`{imageId, url, ...}`). Returns plain URLs."""
    out: list[str] = []
    if not isinstance(image_urls, list):
        return out
    for v in image_urls:
        if isinstance(v, str):
            out.append(v)
        elif isinstance(v, dict):
            url = v.get("url")
            if isinstance(url, str):
                out.append(url)
    return out


# ─── Handlers ───────────────────────────────────────────────────────


async def _async_main() -> None:
    worker = make_worker("maps3d-colmap-worker")

    @task(worker, "maps3d.colmapTile")
    async def colmap_tile(
        tileH3: str,
        selectedIds: list[str] | None = None,
        imageUrls: list[Any] | None = None,
        denseEnabled: bool = True,
        matcher: str = "exhaustive",
        **_: Any,
    ) -> dict[str, Any]:
        urls = _normalize_image_urls(imageUrls or [])
        if not selectedIds or not urls:
            return _failure(tileH3, "TOO_FEW_MATCHES", "no curated images supplied")

        # Filter URL list to selected IDs if both correlate by index.
        # The curator returns selectedIds in the same order as candidates
        # but we don't have a selectedId → URL map here, so we just take
        # the first len(selectedIds) URLs (curator output is descending
        # utility, so prefix is the right slice).
        urls = urls[: len(selectedIds)]

        work_dir = SCRATCH_DIR / tileH3
        cleanup_workdir(work_dir)
        image_dir = work_dir / "images"

        try:
            # Stage 1: download Mapillary thumbnails.
            saved = await _download_images(urls, image_dir, DOWNLOAD_TIMEOUT_S)
            if saved < 3:
                return _failure(
                    tileH3,
                    "TOO_FEW_MATCHES",
                    f"only {saved} images downloaded successfully",
                )

            # Stage 2: COLMAP CPU pipeline.
            res: PipelineResult = await run_pipeline(
                image_dir=image_dir,
                work_dir=work_dir / "colmap",
                colmap_bin=COLMAP_BIN,
                total_budget_s=float(COLMAP_BUDGET_S),
                dense_enabled=bool(denseEnabled),
                matcher=str(matcher or "exhaustive"),
            )

            if not res.ok or res.raw_mesh is None:
                return {
                    "tileH3": tileH3,
                    "ok": False,
                    "imageCount": res.image_count,
                    "reconstructionMs": res.duration_ms,
                    "errorCode": res.error_code or ERR_UNKNOWN,
                    "errorMessage": res.error_message or "",
                }

            # Stage 3: B2 upload of the raw vertex-colored PLY.
            try:
                raw_uri = _b2_client().upload(
                    res.raw_mesh, f"maps3d/raw/{tileH3}.ply"
                )
            except Exception as exc:  # noqa: BLE001
                log.exception("B2 upload failed for %s", tileH3)
                return _failure(tileH3, "UNKNOWN", f"b2 upload: {exc}")

            return {
                "tileH3": tileH3,
                "ok": True,
                "rawMeshUri": raw_uri,
                "imageCount": res.image_count,
                "vertexCount": res.vertex_count,
                "triangleCount": res.triangle_count,
                "reconstructionMs": res.duration_ms,
            }
        finally:
            # Always wipe scratch — colmap pod's emptyDir is shared
            # across tile runs and 50-300 MB per tile would fill it
            # within a day otherwise.
            cleanup_workdir(work_dir)

    @task(worker, "maps3d.simplifyAndExport")
    async def simplify(
        tileH3: str,
        rawMeshUri: str,
        targetTriangles: int = 5000,
        saturate: float = 1.3,
        segmentByFootprint: bool = False,
        **_: Any,
    ) -> dict[str, Any]:
        if segmentByFootprint:
            log.warning(
                "segmentByFootprint=true not implemented; emitting tile-level GLB only"
            )

        work_dir = SCRATCH_DIR / f"simplify-{tileH3}"
        work_dir.mkdir(parents=True, exist_ok=True)
        local_ply = work_dir / "raw.ply"
        local_glb = work_dir / "tile.glb"

        try:
            # Pull the raw PLY back from B2 to /scratch so Open3D can read it.
            try:
                _download_b2_uri(rawMeshUri, local_ply)
            except Exception as exc:  # noqa: BLE001
                log.exception("b2 download failed")
                return {
                    "tileH3": tileH3,
                    "tileMeshUri": "",
                    "buildings": [],
                    "triangleCount": 0,
                    "byteSize": 0,
                    "errorMessage": f"b2 download: {exc}",
                }

            # Quadric decimate → vertex-color GLB.
            from ._mesh import simplify_to_glb

            tri_count, byte_size = await asyncio.wait_for(
                asyncio.to_thread(
                    simplify_to_glb,
                    local_ply,
                    local_glb,
                    target_triangles=int(targetTriangles),
                    saturate=float(saturate),
                ),
                timeout=float(SIMPLIFY_BUDGET_S),
            )

            tile_uri = _b2_client().upload(local_glb, f"maps3d/tile/{tileH3}.glb")
            return {
                "tileH3": tileH3,
                "tileMeshUri": tile_uri,
                "buildings": [],
                "triangleCount": tri_count,
                "byteSize": byte_size,
            }
        except asyncio.TimeoutError:
            return {
                "tileH3": tileH3,
                "tileMeshUri": "",
                "buildings": [],
                "triangleCount": 0,
                "byteSize": 0,
                "errorMessage": f"simplify timed out at {SIMPLIFY_BUDGET_S}s",
            }
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)

    await run_forever(worker)


def main() -> None:
    asyncio.run(_async_main())


def _failure(tile_h3: str, code: str, msg: str) -> dict[str, Any]:
    log.warning("colmapTile FAIL tile=%s code=%s msg=%s", tile_h3, code, msg)
    return {
        "tileH3": tile_h3,
        "ok": False,
        "errorCode": code,
        "errorMessage": msg,
    }


def _download_b2_uri(uri: str, target: Path) -> None:
    """Pull a `b2://bucket/key` URI to a local path. Uses b2sdk, same
    auth context as uploads."""
    if not uri.startswith("b2://"):
        raise ValueError(f"not a b2 URI: {uri!r}")
    rest = uri[len("b2://") :]
    bucket_name, _, key = rest.partition("/")
    if not bucket_name or not key:
        raise ValueError(f"malformed b2 URI: {uri!r}")
    target.parent.mkdir(parents=True, exist_ok=True)
    if bucket_name != B2_BUCKET:
        # Cross-bucket downloads need a fresh client; tolerate but log.
        log.info("b2 cross-bucket download: %s", bucket_name)
        client = B2Client(bucket=bucket_name)
    else:
        client = _b2_client()
    downloaded = client.bucket.download_file_by_name(key)
    downloaded.save_to(str(target))


if __name__ == "__main__":
    main()
