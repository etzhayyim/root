"""social_announce — kaimono-review DID 経由で Bluesky ATPost。"""

from __future__ import annotations

import os

import httpx

from lg_hakken.state import HakkenState

KAIMONO_REVIEW_XRPC = os.environ.get(
    "KAIMONO_REVIEW_XRPC_URL", "https://kaimono-review.etzhayyim.com"
)

_PHASE_LABEL = {
    "dropship": "お試し価格",
    "import":   "国内在庫あり",
    "oem":      "自社ブランド",
}


async def social_announce(state: HakkenState) -> dict:
    """承認SKUを kaimono-review の home カテゴリ DID で Bluesky 投稿。"""
    approved = state.get("approved_skus", [])
    errors: list[str] = list(state.get("errors", []))

    async with httpx.AsyncClient(timeout=30) as client:
        for sku in approved:
            candidate = sku["oem_candidate"]
            label = _PHASE_LABEL.get(sku["phase"], "")
            text = (
                f"【新着 {label}】{candidate['name']}\n"
                f"ブランド品比 {sku['margin']:.0%}オフ · "
                f"評価 {sku['review_score']['grade']}({sku['review_score']['score']}点)\n"
                f"okaimono.etzhayyim.com で販売中"
            )
            try:
                await client.post(
                    f"{KAIMONO_REVIEW_XRPC}/xrpc/com.etzhayyim.apps.kaimono_review.postAnnouncement",
                    json={"category": "home", "text": text},
                )
            except Exception as exc:
                errors.append(f"social_announce: {exc}")

    return {"errors": errors}
