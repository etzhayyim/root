"""(4) validate_training_data: filter teacher outputs per ADR §4 table.

Charter Rider §2 content scan is delegated to charter_rider_scan() —
TODO: integrate the actual scanner from 70-tools/charter-rider-applicator/.
"""

from __future__ import annotations

import json
import re

from ..state import DistillState, TrainExample

_PII_RX = re.compile(
    r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"          # email
    r"|\b\+?\d{1,3}[\s-]?\(?\d{2,4}\)?[\s-]?\d{2,4}[\s-]?\d{2,4}\b"  # phone-ish
)


def _charter_rider_scan(text: str) -> tuple[bool, str]:
    """Delegates to the canonical §2(a)..(h) scanner in
    `etzhayyim_organism.sensors.charter_rider` (per ADR-2605192200 v2.0).
    The import is lazy so a missing organism dep doesn't break import
    of validate.py at module load time."""
    try:
        from etzhayyim_organism.sensors.charter_rider import scan  # type: ignore
    except ImportError:
        # Fall-back: only the smallest sane subset to keep the loop functional
        # in environments where etzhayyim-organism is not on the path.
        lower = text.lower()
        for term in ("buy now", "limited offer", "discount code",
                     "affiliate link", "promo code"):
            if term in lower:
                return False, f"§2(c) (fallback) advertising term: {term!r}"
        return True, "ok (fallback scanner — install etzhayyim-organism for full coverage)"

    r = scan(text)
    return r.ok, r.reason()


def _validate_one(ex: TrainExample) -> tuple[bool, str]:
    if not (8 <= len(ex.response) <= 1024):
        return False, f"length {len(ex.response)} outside [8,1024]"
    if _PII_RX.search(ex.response):
        return False, "PII heuristic match"
    ok, reason = _charter_rider_scan(ex.response)
    if not ok:
        return False, reason

    if ex.category == "IFEval":
        try:
            d = json.loads(_extract_json(ex.response))
            for k in ("prompt", "response", "constraint_type"):
                if k not in d:
                    return False, f"IFEval missing key: {k}"
        except Exception as e:
            return False, f"IFEval json parse: {e}"

    elif ex.category == "MMLU":
        try:
            d = json.loads(_extract_json(ex.response))
            for k in ("q", "A", "B", "C", "D", "correct"):
                if k not in d:
                    return False, f"MMLU missing key: {k}"
            if d["correct"] not in ("A", "B", "C", "D"):
                return False, f"MMLU correct={d['correct']!r}"
        except Exception as e:
            return False, f"MMLU json parse: {e}"

    elif ex.category == "Reasoning":
        if "Answer:" not in ex.response and not re.search(r"\b\d+\b", ex.response[-50:]):
            return False, "Reasoning missing final answer marker"

    elif ex.category == "Multilingual":
        try:
            d = json.loads(_extract_json(ex.response))
            if not d.get("en") or not d.get("ja"):
                return False, "Multilingual empty side"
        except Exception as e:
            return False, f"Multilingual json parse: {e}"

    return True, "ok"


def _extract_json(text: str) -> str:
    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    return m.group(0) if m else text


def validate_training_data(state: DistillState) -> DistillState:
    state.setdefault("notes", []).append("[validate] filtering")

    raw = state.get("training_examples", [])
    if not raw:
        state["notes"].append("[validate] no raw examples — abort")
        state["decision"] = "abort"
        return state

    kept: list[TrainExample] = []
    drop_reasons: dict[str, int] = {}
    for ex in raw:
        ok, reason = _validate_one(ex)
        if ok:
            kept.append(ex)
        else:
            drop_reasons[reason] = drop_reasons.get(reason, 0) + 1

    state["training_examples"] = kept
    pass_rate = len(kept) / max(1, len(raw))
    state["notes"].append(
        f"[validate] kept {len(kept)}/{len(raw)} = {100*pass_rate:.1f}% — "
        f"top drop reasons: "
        + ", ".join(f"{r}×{n}" for r, n in
                    sorted(drop_reasons.items(), key=lambda x: -x[1])[:3])
    )

    if pass_rate < 0.60:
        state["notes"].append(
            "[validate] pass-rate below 60% — flagging teacher as too weak; "
            "decision = retry (different teacher next iter)"
        )
        state["decision"] = "retry"
    return state
