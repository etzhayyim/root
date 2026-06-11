"""maps3d.visionAnnotate + maps3d.linkActor.

visionAnnotate: proxy to Murakumo Vision (qwen3-vl-8b) once wired; today
returns an empty detection list so the BPMN flow completes cleanly.

linkActor: LangGraph multi-source disambiguation (Wikidata SPARQL + GLEIF
+ OSM + LLM judge). Phase 2 scaffold returns no links — the BPMN
correctly handles an empty `links[]` (ingest task simply doesn't write
edges for unlinked detections).
"""

from __future__ import annotations

import asyncio
from typing import Any

from ._common import log, make_worker, run_forever, task


async def _async_main() -> None:
    worker = make_worker("maps3d-langgraph-actor-link")

    @task(worker, "maps3d.visionAnnotate")
    async def vision(
        tileH3: str,
        imageRefs: list[str] | None = None,
        minConfidence: float = 0.55,
        kindAllowlist: list[str] | None = None,
        **_: Any,
    ) -> dict[str, Any]:
        # TODO: real Murakumo client + parallel image inference.
        log.info(
            "visionAnnotate stub tile=%s images=%d minConf=%.2f",
            tileH3,
            len(imageRefs or []),
            minConfidence,
        )
        await asyncio.sleep(0.02)
        return {"tileH3": tileH3, "detections": []}

    @task(worker, "maps3d.linkActor")
    async def link(
        tileH3: str,
        detections: list[dict[str, Any]] | None = None,
        minConfidence: float = 0.7,
        **_: Any,
    ) -> dict[str, Any]:
        # TODO: LangGraph (wikidata_search → gleif_lookup → osm_operator
        # → llm_disambiguate). For now no links — BPMN handles empty.
        log.info(
            "linkActor stub tile=%s detections=%d minConf=%.2f",
            tileH3,
            len(detections or []),
            minConfidence,
        )
        return {"tileH3": tileH3, "links": []}

    await run_forever(worker)


def main() -> None:
    asyncio.run(_async_main())


if __name__ == "__main__":
    main()
