"""okaimono_register — LP自動生成 + Stripe 商品作成 (全Phase共通)。"""

from __future__ import annotations

import os

import httpx

from lg_hakken.state import HakkenState

OKAIMONO_XRPC = os.environ.get("OKAIMONO_XRPC_URL", "https://okaimono.etzhayyim.com")


async def okaimono_register(state: HakkenState) -> dict:
    """既に dropship/import/oem ノードで登録済みのSKUに対してStripe商品を紐付け。"""
    ids = state.get("registered_okaimono_ids", [])
    errors: list[str] = list(state.get("errors", []))

    if not ids:
        return {}

    async with httpx.AsyncClient(timeout=30) as client:
        for item_id in ids:
            if not item_id:
                continue
            try:
                resp = await client.post(
                    f"{OKAIMONO_XRPC}/xrpc/com.etzhayyim.apps.okaimono.publishCatalogItem",
                    json={"item_id": item_id},
                )
                if not resp.is_success:
                    errors.append(f"okaimono_register publish failed: {item_id}")
            except Exception as exc:
                errors.append(f"okaimono_register: {exc}")

    return {"errors": errors}
