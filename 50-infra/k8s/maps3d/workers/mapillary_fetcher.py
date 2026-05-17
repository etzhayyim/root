"""maps3d.fetchMapillary — Mapillary v4 candidate set for an H3 tile.

Phase 2 scope: real Mapillary v4 calls + B2 caching are deferred. This
worker today returns a deterministic synthetic candidate set so the
upstream BPMN gateway logic + LangGraph curator can be validated
end-to-end before we burn Mapillary quota.

Real implementation outline (next iteration):
    1. h3.cell_to_boundary(tileH3) → bbox
    2. GET https://graph.mapillary.com/images?bbox=...&fields=id,geometry,
       compass_angle,captured_at,thumb_2048_url,quality_score
    3. filter quality_score, captured_at age, dedupe by camera_pose hash
    4. return as `candidates` list matching the lexicon shape
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

from ._common import log, make_worker, run_forever, task


def _stub_candidates(tile_h3: str, max_images: int) -> list[dict[str, Any]]:
    """Deterministic synthetic candidates so downstream tasks can run
    even before Mapillary credentials are wired up."""
    n = min(max_images, 30)
    return [
        {
            "imageId": f"stub-{tile_h3}-{i:03d}",
            "lat": 35.6812,
            "lng": 139.7671,
            "compassAngle": (i * 12.0) % 360.0,
            "altitude": 5.0,
            "capturedAt": "2026-01-01T00:00:00Z",
            "qualityScore": 0.85,
            "url": f"https://example.invalid/mapillary/stub/{tile_h3}/{i}.jpg",
        }
        for i in range(n)
    ]


async def _async_main() -> None:
    """Build the worker + register handlers from inside the event loop."""
    worker = make_worker("maps3d-mapillary-fetcher")

    @task(worker, "maps3d.fetchMapillary")
    async def fetch(
        tileH3: str,
        maxImages: int = 200,
        minQuality: float = 0.5,
        lookbackDays: int = 1825,
        **_: Any,
    ) -> dict[str, Any]:
        token = os.environ.get("MAPILLARY_TOKEN")
        if not token:
            log.warning(
                "MAPILLARY_TOKEN unset — returning stub candidates for tile=%s",
                tileH3,
            )
        # TODO: replace with real Mapillary fetch + quality/recency filter.
        candidates = _stub_candidates(tileH3, maxImages)
        return {
            "tileH3": tileH3,
            "candidates": candidates,
            "totalAvailable": len(candidates),
        }

    await run_forever(worker)


def main() -> None:
    asyncio.run(_async_main())


if __name__ == "__main__":
    main()
