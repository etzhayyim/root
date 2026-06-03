"""phase_router — weight / margin / rating からSKUのフェーズを決定。"""

from __future__ import annotations

from lg_hakken.state import ApprovedSku, HakkenState, OemCandidate

HEAVY_KG = 5.0          # これ以上はPh1 dropship不可 → Ph2から
MIN_MARGIN_DROP = 0.30  # Ph1 dropship 最低粗利
MIN_MARGIN_IMPORT = 0.60
MIN_MARGIN_OEM = 0.60
MIN_RATING_DROP = 4.0
MIN_RATING_IMPORT = 4.5
MIN_GRADE_DROP = "B"    # kaimono-review 最低合格グレード

_GRADE_ORDER = {"S": 5, "A": 4, "B": 3, "C": 2, "D": 1}


def _margin(branded_price: int, oem_price: int) -> float:
    if branded_price <= 0:
        return 0.0
    return 1.0 - oem_price / branded_price


def _grade_ok(grade: str, min_grade: str) -> bool:
    return _GRADE_ORDER.get(grade, 0) >= _GRADE_ORDER.get(min_grade, 0)


async def phase_router(state: HakkenState) -> dict:
    """各 OEM候補に対してフェーズを判定し approved_skus に積む。"""
    candidates: list[OemCandidate] = state.get("oem_candidates", [])
    branded_map = {p["name"]: p for p in state.get("branded_products", [])}
    scores = state.get("review_scores", {})
    approved: list[ApprovedSku] = []

    for candidate in candidates:
        score = scores.get(candidate["item_id"])
        if not score:
            continue
        if not _grade_ok(score["grade"], MIN_GRADE_DROP):
            continue

        branded = branded_map.get(candidate.get("equivalent_of") or "")
        if branded is None:
            continue
        margin = _margin(branded["price_jpy"], candidate["price_jpy"])

        # 重量物 → Ph2から (dropship不可)
        if candidate["weight_kg"] > HEAVY_KG:
            if margin >= MIN_MARGIN_IMPORT and candidate["rating"] >= MIN_RATING_IMPORT:
                phase = "import"
            else:
                continue  # 条件未達、スキップ
        elif margin >= MIN_MARGIN_OEM and candidate["rating"] >= MIN_RATING_IMPORT:
            phase = "oem"
        elif margin >= MIN_MARGIN_DROP and candidate["rating"] >= MIN_RATING_DROP:
            phase = "dropship"
        else:
            continue  # 条件未達、スキップ

        sell_price = _target_price(candidate["price_jpy"], phase)
        approved.append(
            ApprovedSku(
                oem_candidate=candidate,
                branded_product=branded or {},
                margin=margin,
                phase=phase,
                review_score=score,
                sell_price_jpy=sell_price,
            )
        )

    return {"approved_skus": approved}


def route_by_phase(state: HakkenState) -> str:
    """conditional_edges 用のルーティング関数。"""
    approved = state.get("approved_skus", [])
    if not approved:
        return "end"
    # 先頭SKUのフェーズに基づいてルーティング (複数SKUは同一パスで処理)
    return approved[0]["phase"]


def _target_price(oem_price: int, phase: str) -> int:
    """販売価格を粗利目標から逆算。Ph1: 2.5x, Ph2: 2.8x, Ph3: 3.5x."""
    multiplier = {"dropship": 2.5, "import": 2.8, "oem": 3.5}.get(phase, 2.5)
    raw = int(oem_price * multiplier)
    # 末尾を 800 に丸める (¥6,800, ¥12,800 etc.)
    return (raw // 1000) * 1000 + 800
