"""quality_eval — kaimono-review XRPC で5軸スコアリング。"""

from __future__ import annotations

import os

import httpx

from lg_hakken.state import HakkenState, OemCandidate, ReviewScore

KAIMONO_REVIEW_XRPC = os.environ.get(
    "KAIMONO_REVIEW_XRPC_URL", "https://kaimono-review.etzhayyim.com"
)

# 最低合格グレード (B = 60点以上)
MIN_GRADE = "B"


async def quality_eval(state: HakkenState) -> dict:
    """kaimono-review XRPC で各OEM候補をスコアリングし review_scores に積む。"""
    candidates: list[OemCandidate] = state.get("oem_candidates", [])
    scores: dict[str, ReviewScore] = {}

    async with httpx.AsyncClient(timeout=60) as client:
        for candidate in candidates:
            try:
                resp = await client.post(
                    f"{KAIMONO_REVIEW_XRPC}/xrpc/com.etzhayyim.apps.kaimono_review.scoreProduct",
                    json={
                        "name":       candidate["name"],
                        "platform":   candidate["platform"],
                        "item_id":    candidate["item_id"],
                        "material":   candidate.get("material"),
                        "washable":   candidate.get("washable"),
                        "rating":     candidate["rating"],
                        "review_count": candidate["review_count"],
                    },
                )
                if resp.is_success:
                    data = resp.json()
                    scores[candidate["item_id"]] = ReviewScore(
                        item_id=candidate["item_id"],
                        grade=data.get("grade", "C"),
                        score=data.get("score", 0),
                        quality=data.get("quality", 0.0),
                        usability=data.get("usability", 0.0),
                        cost_performance=data.get("cost_performance", 0.0),
                        satisfaction=data.get("satisfaction", 0.0),
                        sustainability=data.get("sustainability", 0.0),
                    )
                else:
                    # XRPC未実装時はレーティングからスコアを推定
                    scores[candidate["item_id"]] = _estimate_score(candidate)
            except Exception:
                scores[candidate["item_id"]] = _estimate_score(candidate)

    return {"review_scores": scores}


def _estimate_score(candidate: OemCandidate) -> ReviewScore:
    """XRPC 未接続時のスコア推定 (rating × 20 で0-100換算)。"""
    raw = candidate["rating"]
    score = int(min(raw * 20, 100))
    grade = "S" if score >= 90 else "A" if score >= 75 else "B" if score >= 60 else "C"
    return ReviewScore(
        item_id=candidate["item_id"],
        grade=grade,
        score=score,
        quality=raw / 5.0,
        usability=raw / 5.0,
        cost_performance=0.8,
        satisfaction=raw / 5.0,
        sustainability=0.7,
    )
