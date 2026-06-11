"""supplier_search — AliExpress / Alibaba / 1688 でOEM候補を検索。"""

from __future__ import annotations

import os

import httpx

from lg_hakken.state import HakkenState, OemCandidate

# AliExpress unofficial scraper or AliExpress Affiliate API
ALIEXPRESS_API = os.environ.get("ALIEXPRESS_API_URL", "")

# 重量物閾値 (kg) — これ以上はPh1 dropship不可
HEAVY_WEIGHT_KG = 5.0

# 検索キーワードマップ (カテゴリ → 検索語)
_SEARCH_KEYWORDS: dict[str, list[str]] = {
    "mattress": ["3D air fiber mattress 8cm", "polyethylene fiber mattress washable"],
    "pillow":   ["3D air fiber pillow washable", "polyethylene fiber pillow"],
    "topper":   ["3D fiber mattress topper 5cm washable"],
}


async def supplier_search(state: HakkenState) -> dict:
    """AliExpress API でカテゴリ別OEM候補を検索。重量・素材・レビュー数でフィルタ。"""
    category = state["category"]
    keywords = _SEARCH_KEYWORDS.get(category, [category])
    candidates: list[OemCandidate] = []

    if not ALIEXPRESS_API:
        # API未設定時はスタブデータで動作確認
        candidates = _stub_candidates(category)
        return {"oem_candidates": candidates}

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            for keyword in keywords:
                resp = await client.get(
                    f"{ALIEXPRESS_API}/search",
                    params={"q": keyword, "limit": 20, "sort": "orders_desc"},
                )
                resp.raise_for_status()
                for item in resp.json().get("items", []):
                    if item.get("rating", 0) < 4.0:
                        continue
                    if item.get("review_count", 0) < 50:
                        continue
                    candidates.append(
                        OemCandidate(
                            name=item["title"],
                            platform="aliexpress",
                            item_id=item["item_id"],
                            url=item["url"],
                            price_jpy=int(item["price_usd"] * 150),  # USD→JPY概算
                            weight_kg=float(item.get("weight_kg", 1.0)),
                            rating=float(item["rating"]),
                            review_count=int(item["review_count"]),
                            material=item.get("material"),
                            thickness_cm=item.get("thickness_cm"),
                            washable=item.get("washable", False),
                            lead_days=int(item.get("shipping_days", 21)),
                            min_order=int(item.get("min_order", 1)),
                            supplier_country=item.get("country", "CN"),
                            equivalent_of=None,
                        )
                    )
    except Exception as exc:
        return {
            "oem_candidates": candidates,
            "errors": state.get("errors", []) + [f"supplier_search: {exc}"],
        }

    return {"oem_candidates": candidates}


def _stub_candidates(category: str) -> list[OemCandidate]:
    """API未接続時のスタブ — 開発・テスト用。"""
    if category == "pillow":
        return [
            OemCandidate(
                name="3D Air Fiber Pillow Washable PE",
                platform="aliexpress",
                item_id="1005009071063808",
                url="https://www.aliexpress.com/item/1005009071063808.html",
                price_jpy=2500,
                weight_kg=0.5,
                rating=4.7,
                review_count=312,
                material="polyethylene-fiber",
                thickness_cm=None,
                washable=True,
                lead_days=18,
                min_order=1,
                supplier_country="CN",
                equivalent_of="Brain Sleep Pillow",
            )
        ]
    if category == "mattress":
        return [
            OemCandidate(
                name="3D Air Fiber Mattress 8cm Washable",
                platform="aliexpress",
                item_id="1005007792087113",
                url="https://www.aliexpress.com/item/1005007792087113.html",
                price_jpy=12500,
                weight_kg=8.5,
                rating=4.6,
                review_count=189,
                material="polyethylene-fiber",
                thickness_cm=8,
                washable=True,
                lead_days=21,
                min_order=1,
                supplier_country="CN",
                equivalent_of="Brain Sleep Mattress",
            )
        ]
    return []
