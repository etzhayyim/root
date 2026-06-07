"""(3) validate: length / parse / Charter Rider §2 scan.

Per ADR-2605250400 §2: every example must pass the Charter Rider §2(a)-(h)
scanner. Violations are dropped silently with a counter.

The canonical scanner lives at:
  kotodama.organism.sensors.charter_rider.scan(text) -> ScanResult

If the scanner isn't importable (kotodama not installed in this venv),
fall back to a coarse keyword filter and log the gap. This mirrors
baien-distill's degradation path.
"""

from __future__ import annotations

from ..state import DistillState, TrainExample

MIN_PROMPT_CHARS = 20
MAX_PROMPT_CHARS = 8000
MAX_RESPONSE_CHARS = 16000


def _coarse_filter(text: str) -> bool:
    """Last-ditch keyword filter if Charter Rider scanner unavailable.

    Returns True if text passes (no obvious violation), False to drop.
    """
    lo = text.lower()
    banned = [
        "child sexual", "csam",
        "non-consensual",
        "weapon design", "bioweapon",
        "rapture", "end times prophecy",
    ]
    return not any(b in lo for b in banned)


def validate(state: DistillState) -> DistillState:
    state.setdefault("notes", []).append("[validate] starting")

    examples: list[TrainExample] = state.get("training_examples", [])
    if not examples:
        state["notes"].append("[validate] no examples — abort")
        state["decision"] = "abort"
        return state

    scan = None
    try:
        from kotodama.organism.sensors.charter_rider import scan as _s  # type: ignore
        scan = _s
        state["notes"].append("[validate] using kotodama Charter Rider scanner")
    except Exception:
        state["notes"].append(
            "[validate] WARN kotodama unavailable — coarse keyword filter only"
        )

    kept: list[TrainExample] = []
    dropped_len = 0
    dropped_rider = 0
    for ex in examples:
        if not (MIN_PROMPT_CHARS <= len(ex.prompt) <= MAX_PROMPT_CHARS):
            dropped_len += 1
            continue
        if len(ex.response) > MAX_RESPONSE_CHARS:
            dropped_len += 1
            continue

        combined = f"{ex.prompt}\n{ex.response}"
        if scan is not None:
            res = scan(combined)
            if not getattr(res, "ok", True):
                dropped_rider += 1
                continue
        else:
            if not _coarse_filter(combined):
                dropped_rider += 1
                continue
        kept.append(ex)

    state["training_examples"] = kept
    state["notes"].append(
        f"[validate] kept={len(kept)} dropped_len={dropped_len} "
        f"dropped_rider={dropped_rider}"
    )
    state["decision"] = "continue" if kept else "abort"
    return state
