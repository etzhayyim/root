"""okaimono_dropship — Ph1: okaimono に AliExpress dropship 商品として登録。"""

from __future__ import annotations

import os

import httpx

from lg_hakken.state import ApprovedSku, HakkenState

OKAIMONO_XRPC = os.environ.get("OKAIMONO_XRPC_URL", "https://okaimono.etzhayyim.com")


async def okaimono_dropship(state: HakkenState) -> dict:
    """承認済みSKUを okaimono にdropship商品として登録。AliExpress item_id を dropship_source に設定。"""
    approved: list[ApprovedSku] = state.get("approved_skus", [])
    registered: list[str] = list(state.get("registered_okaimono_ids", []))
    errors: list[str] = list(state.get("errors", []))

    async with httpx.AsyncClient(timeout=30) as client:
        for sku in approved:
            if sku["phase"] != "dropship":
                continue
            candidate = sku["oem_candidate"]
            try:
                resp = await client.post(
                    f"{OKAIMONO_XRPC}/xrpc/com.etzhayyim.apps.okaimono.createCatalogItem",
                    json={
                        "name":           candidate["name"],
                        "category":       state["category"],
                        "price":          sku["sell_price_jpy"],
                        "fulfillment":    "dropship",
                        "dropship_source": {
                            "platform": "aliexpress",
                            "item_id":  candidate["item_id"],
                            "url":      candidate["url"],
                        },
                        "lead_days":      candidate["lead_days"],
                        "review_score":   sku["review_score"]["score"],
                        "review_grade":   sku["review_score"]["grade"],
                    },
                )
                if resp.is_success:
                    registered.append(resp.json().get("item_id", ""))
                else:
                    errors.append(f"okaimono_dropship register failed: {resp.status_code} {candidate['item_id']}")
            except Exception as exc:
                errors.append(f"okaimono_dropship: {exc}")

    return {"registered_okaimono_ids": registered, "errors": errors}
