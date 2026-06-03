"""import_order — Ph2: Alibaba 小ロット輸入発注 (stub)。"""

from __future__ import annotations

from lg_hakken.state import HakkenState


async def import_order(state: HakkenState) -> dict:
    """Ph2: 小ロット輸入発注。現在はオペレーターへの通知のみ (manual approval required)。

    TODO: tsukuru.etzhayyim.com に輸入調達 XRPC を実装後に自動化。
    """
    approved = [s for s in state.get("approved_skus", []) if s["phase"] == "import"]
    notifications = []
    for sku in approved:
        candidate = sku["oem_candidate"]
        notifications.append(
            f"[Ph2 Import Required] {candidate['name']} "
            f"item_id={candidate['item_id']} "
            f"price_jpy={candidate['price_jpy']} "
            f"weight_kg={candidate['weight_kg']}"
        )

    # TODO: ops Slack/Teams 通知を実装
    for note in notifications:
        print(note)

    return {}
