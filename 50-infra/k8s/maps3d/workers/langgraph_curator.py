"""maps3d.curateImages + maps3d.replanReconstruction — LangGraph nodes.

Phase 2 scaffold: deterministic heuristic stubs. The full LangGraph
graph (score_quality → score_coverage → llm_dedupe → decide_count) goes
in next once we have real Mapillary candidates flowing.

The curator picks ~30 images with maximum azimuthal diversity from the
candidate set (real version uses LangGraph + Murakumo Vision LLM). The
replanner today emits a single decision: downgrade-to-osm on any
COLMAP failure, since multi-pass replanning is deferred until we have
steady-state failure-rate data.
"""

from __future__ import annotations

import asyncio
from typing import Any

from ._common import log, make_worker, run_forever, task


def _diverse_pick(
    candidates: list[dict[str, Any]], target: int
) -> tuple[list[str], str]:
    """Greedy azimuthal diversity. Real LangGraph version adds quality
    score + LLM dedupe + per-baseline scoring."""
    if not candidates:
        return [], "no candidates supplied"
    # Sort by qualityScore desc, then take every Nth to spread coverage.
    sorted_c = sorted(
        candidates,
        key=lambda c: (-(c.get("qualityScore") or 0.0), c.get("compassAngle") or 0.0),
    )
    if len(sorted_c) <= target:
        ids = [c["imageId"] for c in sorted_c]
        return ids, f"all {len(ids)} candidates kept (≤ target {target})"
    step = max(1, len(sorted_c) // target)
    picked = sorted_c[::step][:target]
    ids = [c["imageId"] for c in picked]
    return ids, f"strided pick (step {step}) from {len(sorted_c)} cands → {len(ids)}"


async def _async_main() -> None:
    worker = make_worker("maps3d-langgraph-curator")

    @task(worker, "maps3d.curateImages")
    async def curate(
        tileH3: str,
        candidates: list[dict[str, Any]] | None = None,
        targetCount: int = 30,
        minCount: int = 8,
        **_: Any,
    ) -> dict[str, Any]:
        candidates = candidates or []
        ids, reason = _diverse_pick(candidates, targetCount)
        abort = len(ids) < minCount
        if abort:
            log.warning(
                "curateImages tile=%s aborting: %d < min %d",
                tileH3,
                len(ids),
                minCount,
            )
        return {
            "tileH3": tileH3,
            "selectedIds": ids,
            "selectedCount": len(ids),
            "reason": reason,
            "abort": abort,
        }

    @task(worker, "maps3d.replanReconstruction")
    async def replan(
        tileH3: str,
        errorCode: str,
        errorMessage: str = "",
        imageCount: int = 0,
        attempt: int = 1,
        **_: Any,
    ) -> dict[str, Any]:
        # Bounded multi-attempt policy.
        #   attempt 1 — try to recover with cheaper or larger inputs:
        #     TIMEOUT / DENSE_OOM    → retry sparse-only (denseEnabled=false)
        #     BUNDLE_DIVERGED        → retry as-is (mapper sometimes
        #                              flaps on the same inputs and
        #                              succeeds the second time)
        #     TOO_FEW_MATCHES        → requestMore (more Mapillary
        #                              candidates next pass)
        #     UNKNOWN                → retry as-is (single free retry)
        #   attempt >=2 — every failure exits via downgradeOsm so the
        #     UI keeps the tile visible via the Phase-1 OSM extrude
        #     path. We never `abort` with the row stuck `failed` — that
        #     would brick the tile until manual SQL reset.
        action: str
        retry_hints: dict[str, Any] = {}
        if attempt < 2:
            if errorCode in ("TIMEOUT", "DENSE_OOM"):
                action = "retry"
                retry_hints = {"denseEnabled": False, "matcher": "exhaustive"}
            elif errorCode == "BUNDLE_DIVERGED":
                action = "retry"
                retry_hints = {"denseEnabled": True, "matcher": "exhaustive"}
            elif errorCode == "TOO_FEW_MATCHES":
                action = "requestMore"
                retry_hints = {"maxImages": 400, "minQuality": 0.4}
            else:
                # UNKNOWN — give it one more shot with the same inputs.
                action = "retry"
                retry_hints = {"denseEnabled": True, "matcher": "exhaustive"}
        else:
            # Second failure — give up on photogrammetry for this tile,
            # fall back to OSM extrude. Tile stays visible in the UI.
            action = "downgradeOsm"
        log.info(
            "replan tile=%s code=%s images=%d attempt=%d → %s hints=%s",
            tileH3,
            errorCode,
            imageCount,
            attempt,
            action,
            retry_hints,
        )
        return {
            "tileH3": tileH3,
            "action": action,
            "retryHints": retry_hints,
            "rationale": (
                f"attempt={attempt} errorCode={errorCode} → {action} "
                f"(bounded ≤ 2 attempts; downgradeOsm is the terminal fallback)"
            ),
        }

    await run_forever(worker)


def main() -> None:
    asyncio.run(_async_main())


if __name__ == "__main__":
    main()
