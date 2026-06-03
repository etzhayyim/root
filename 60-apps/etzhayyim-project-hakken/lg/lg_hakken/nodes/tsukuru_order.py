"""tsukuru_order — Ph3: tsukuru.etzhayyim.com 経由でOEM製造発注 (stub)。"""

from __future__ import annotations

from lg_hakken.state import HakkenState


async def tsukuru_order(state: HakkenState) -> dict:
    """Ph3: OEM製造発注。tsukuru XRPC が実装されるまでオペレーター通知のみ。

    TODO: com.etzhayyim.apps.tsukuru.createManufacturingOrder XRPC 実装後に自動化。
    """
    approved = [s for s in state.get("approved_skus", []) if s["phase"] == "oem"]
    for sku in approved:
        candidate = sku["oem_candidate"]
        print(
            f"[Ph3 OEM Order Required] {candidate['name']} "
            f"supplier_item={candidate['item_id']} "
            f"margin={sku['margin']:.0%}"
        )

    return {}
