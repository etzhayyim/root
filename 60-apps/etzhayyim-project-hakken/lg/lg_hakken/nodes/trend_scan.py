"""trend_scan — Bluesky/X/Insta トレンドから商品カテゴリの需要シグナルを収集。"""

from __future__ import annotations

import os

import httpx

from lg_hakken.state import BrandedProduct, HakkenState

KAKAKU_XRPC = os.environ.get("KAKAKU_XRPC_URL", "https://kakaku.etzhayyim.com")


async def trend_scan(state: HakkenState) -> dict:
    """kakaku XRPC からカテゴリ内ブランド品一覧を取得してstateに積む。"""
    category = state["category"]
    branded: list[BrandedProduct] = []

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{KAKAKU_XRPC}/xrpc/com.etzhayyim.apps.kakaku.listOffers",
                params={"category": category, "limit": 50},
            )
            resp.raise_for_status()
            data = resp.json()
            for item in data.get("offers", []):
                branded.append(
                    BrandedProduct(
                        name=item["name"],
                        brand=item.get("brand", ""),
                        category=category,
                        price_jpy=item["price"],
                        url=item.get("url", ""),
                        material=item.get("material"),
                    )
                )
    except Exception as exc:
        return {"branded_products": branded, "errors": state.get("errors", []) + [f"trend_scan: {exc}"]}

    return {"branded_products": branded}
