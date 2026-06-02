#!/usr/bin/env python3
"""silicon 珪 — fab-orchestration kotoba agent (gate-enforcing, R0).

ADR-2605242500 / 2605242545 · ADR-2606021139. Complements the per-process langgraph
cells (cells/{mask_lithography,wafer_processing,chiptest,packaging}) with the
kotoba-facing concerns: append-only lot traceability (G8), the §2(a)(c) force-review
gate (G1), and chip inalienability (G2 — chips are LEASED, never sold). Pure
compute; it records attestation datoms and decides gates. It does NOT dispatch real
fab equipment — that is Council-ratification + force-review gated (the langgraph
cells raise on .solve()). No platform key is held (G7); operator/Council DIDs sign.

LLM access, if any, is Murakumo-only (ADR-2605215000); this module needs none.
"""
from __future__ import annotations

# 8 fab process steps (lexicon knownValues, ADR-2605242545)
PROCESS_STEPS = ["litho", "deposition", "etch", "implant", "cmp", "metrology", "test", "packaging"]
# steps that carry HIGH §2(a)(c) weapons/surveillance-diversion risk → force-review REQUIRED (G1)
FORCE_REVIEW_REQUIRED = {"litho", "implant"}
# verdicts that permit a gated step to proceed
CLEARING_VERDICTS = {"approve", "approve-with-conditions"}


# --------------------------------------------------------------------------- #
# G1 — §2(a)(c) force-review gate
# --------------------------------------------------------------------------- #
def force_review_gate(process: str, review: dict | None) -> dict:
    """Decide whether a process step may run. litho/implant require a force-review with
    a clearing verdict; an unresolved/denied review blocks (never auto-passes, G1)."""
    if process not in FORCE_REVIEW_REQUIRED:
        return {"allowed": True, "reason": "not a §2(a)(c)-gated step"}
    if not review:
        return {"allowed": False, "reason": f"{process} requires a silenForceReview (G1)"}
    verdict = review.get("verdict")
    if verdict in CLEARING_VERDICTS:
        return {"allowed": True, "reason": f"force-review {verdict}"}
    return {"allowed": False, "reason": f"force-review verdict '{verdict}' does not clear (G1)"}


# --------------------------------------------------------------------------- #
# G8 — append-only lot traceability
# --------------------------------------------------------------------------- #
def record_process_step(lot: dict, process: str, equipment_did: str,
                        completed_at: str, review: dict | None = None,
                        outcome: str = "ok") -> dict:
    """Append one process-step attestation to a lot's history. Enforces the force-review
    gate (G1) and monotonic step indexing (G8 — never rewrites prior steps)."""
    if process not in PROCESS_STEPS:
        return {"error": f"unknown process '{process}'"}
    gate = force_review_gate(process, review)
    if not gate["allowed"]:
        return {"error": gate["reason"], "blocked": True}
    history = list(lot.get("history", []))
    step_index = len(history)
    step = {
        "stepIndex": step_index,
        "process": process,
        "equipmentDid": equipment_did,
        "outcome": outcome,
        "completedAt": completed_at,
    }
    if review:
        step["forceReviewUri"] = review.get("id", "")
    history.append(step)
    state = "verified" if (process == "packaging" and outcome == "ok") else lot.get("state", "in-fab")
    if outcome in ("scrapped", "quarantined"):
        state = outcome
    return {**lot, "history": history, "currentStepIndex": step_index, "state": state}


def lot_traceable(lot: dict) -> bool:
    """A lot is traceable iff its step indices form a gap-free monotonic 0..n chain (G8)."""
    idx = [s.get("stepIndex") for s in lot.get("history", [])]
    return idx == list(range(len(idx)))


# --------------------------------------------------------------------------- #
# G2 — chip inalienability (LEASE only, never sell/transfer)
# --------------------------------------------------------------------------- #
def lease_chip(chip: dict, lessee_did: str, force_review_uri: str | None) -> dict:
    """Lease a manufactured die to an SBT-holder. A chip is never owned/sold/transferred
    (land-trust-analogue inalienability, G2). Ship requires a force-review (G1)."""
    if not force_review_uri:
        return {"error": "ship/lease requires a force-review (G1)", "blocked": True}
    return {**chip, "leasedToDid": lessee_did, "forceReviewUri": force_review_uri}


def assert_no_transfer(action: str) -> dict:
    """Reject any sale/transfer/burn of silicon assets (G2). Only :lease is permitted."""
    prohibited = {"sell", "transfer", "burn", "set-owner", "gift"}
    if action in prohibited:
        return {"allowed": False,
                "reason": f"'{action}' violates silicon inalienability (G2); only lease-to-SBT is permitted"}
    return {"allowed": action == "lease",
            "reason": "lease permitted" if action == "lease" else f"unknown action '{action}'"}


if __name__ == "__main__":  # pragma: no cover
    lot = {"id": "LOT-DEMO", "history": []}
    review = {"id": "fr.litho", "verdict": "approve"}
    lot = record_process_step(lot, "litho", "equip/litho-01", "2026-06-02T00:00:00Z", review)
    print("after litho:", lot.get("currentStepIndex"), lot.get("state"))
    blocked = record_process_step(lot, "implant", "equip/imp-01", "2026-06-02T01:00:00Z", review=None)
    print("implant without review:", blocked.get("blocked"), blocked.get("error"))
    print("sell attempt:", assert_no_transfer("sell"))
