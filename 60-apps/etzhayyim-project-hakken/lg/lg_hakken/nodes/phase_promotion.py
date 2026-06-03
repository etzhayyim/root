"""phase_promotion — cron: SKU フェーズ昇格を datomic.q (Datalog) で検出し
datomic.transact で更新する。

Read = datomic.q (Datalog EDN) — primary.
Write = datomic.transact ([:db/add E :kg/claim/phase V] — cardinality:one なので
:db/add で原子的置換)。

kg ingest 系は claim 値を文字列で書いている (gap_analysis.py 参照) ため、
Datalog 側で数値 FILTER をかけず、結果を Python 側で型変換 + 閾値判定する。
"""

from __future__ import annotations

import os

import httpx

from lg_hakken.kotoba_datomic import dm_q, dm_transact, encode_tx_data, tx_add
from lg_hakken.state import HakkenState

OKAIMONO_XRPC = os.environ.get("OKAIMONO_XRPC_URL", "https://okaimono.etzhayyim.com")

# Ph1→Ph2: 累積注文≥30件 AND 返品率<5%
# Datalog: phase=":phase/dropship" の SKU と関連 claim を一括取得。
_RULE2_DATALOG = """
[:find ?sku ?okaimonoId ?orders ?rr
 :where
 [?sku :kg/claim/phase ":phase/dropship"]
 [?sku :kg/claim/dropshipOrders ?orders]
 [?sku :kg/claim/returnRate ?rr]
 [?sku :kg/claim/okaimonoId ?okaimonoId]]
"""

# Ph2→Ph3: 月次GMV≥30万 AND 返品率<3% AND マージン見込み≥60%
_RULE3_DATALOG = """
[:find ?sku ?okaimonoId ?gmv ?rr ?mp
 :where
 [?sku :kg/claim/phase ":phase/import"]
 [?sku :kg/claim/monthlyGmv ?gmv]
 [?sku :kg/claim/returnRate ?rr]
 [?sku :kg/claim/marginPotential ?mp]
 [?sku :kg/claim/okaimonoId ?okaimonoId]]
"""


async def phase_promotion(state: HakkenState) -> dict:
    """datomic.q で昇格候補を検出し、datomic.transact で SKU + okaimono を更新。"""
    errors: list[str] = list(state.get("errors", []))

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            # Ph1 → Ph2
            for row in await dm_q(client, _RULE2_DATALOG):
                sku, okaimono_id, orders, rr = row
                if _to_int(orders) >= 30 and _to_float(rr) < 0.05:
                    await _promote(client, sku, okaimono_id,
                                   new_phase=":phase/import", label="import",
                                   errors=errors)

            # Ph2 → Ph3
            for row in await dm_q(client, _RULE3_DATALOG):
                sku, okaimono_id, gmv, rr, mp = row
                if _to_int(gmv) >= 300_000 and _to_float(rr) < 0.03 and _to_float(mp) >= 0.60:
                    await _promote(client, sku, okaimono_id,
                                   new_phase=":phase/oem", label="oem",
                                   errors=errors)

    except Exception as exc:
        errors.append(f"phase_promotion: {exc}")

    return {"errors": errors}


def _to_int(v) -> int:
    try:    return int(str(v))
    except Exception: return 0


def _to_float(v) -> float:
    try:    return float(str(v))
    except Exception: return 0.0


async def _promote(
    client: httpx.AsyncClient,
    sku_id: str,
    okaimono_id: str,
    new_phase: str,
    label: str,
    errors: list[str],
) -> None:
    """Re-assert SKU phase via datomic.transact + update okaimono fulfillment.

    `:kg/claim/phase` is cardinality:one — `[:db/add sku :kg/claim/phase V]`
    replaces the prior value in one tx (no explicit retract needed).
    """
    try:
        tx_edn = encode_tx_data([tx_add(sku_id, "kg/claim/phase", new_phase)])
        await dm_transact(client, tx_edn)

        if okaimono_id:
            await client.post(
                f"{OKAIMONO_XRPC}/xrpc/com.etzhayyim.apps.okaimono.updateFulfillment",
                json={"item_id": okaimono_id, "phase": label},
            )
    except Exception as exc:
        errors.append(f"_promote {sku_id} → {new_phase}: {exc}")
