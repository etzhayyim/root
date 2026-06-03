"""gap_analysis — kotoba datomic.transact でブランド品を KG に登録。"""

from __future__ import annotations

import httpx

from lg_hakken.kotoba_datomic import dm_transact_entities
from lg_hakken.state import BrandedProduct, HakkenState


def _branded_entity(product: BrandedProduct) -> dict:
    """BrandedProduct → datomic transact entity payload."""
    entity_id = f"product:{product['brand']}:{product['name']}"
    return {
        "id":      entity_id,
        "type":    "BrandedProduct",
        "labelJa": product["name"],
        "claims": [
            {"pred": "brand",     "value": product["brand"]},
            {"pred": "category",  "value": product["category"]},
            {"pred": "priceJpy",  "value": str(product["price_jpy"])},
            {"pred": "url",       "value": product["url"]},
        ],
    }


async def gap_analysis(state: HakkenState) -> dict:
    """ブランド品を datomic.transact で kotobase-kg-v1 graph に書く (IPFS pin 永続化)。"""
    cids: list[str] = list(state.get("kotoba_cids", []))
    branded = state.get("branded_products", [])
    errors: list[str] = list(state.get("errors", []))

    if not branded:
        return {"kotoba_cids": cids}

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            entities = [_branded_entity(p) for p in branded]
            # Chunked into <1 MiB EDN strings, chained via expectedParent so
            # the whole batch lands on one lineage.
            results = await dm_transact_entities(client, entities)
            for r in results:
                if t := r.get("tx_cid"):
                    cids.append(t)
    except Exception as exc:
        errors.append(f"gap_analysis: {exc}")
        return {"kotoba_cids": cids, "errors": errors}

    return {"kotoba_cids": cids}
