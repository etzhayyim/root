"""(8) federated_aggregate: gather + verify + merge smartphone-submitted LoRA deltas.

Per ADR-2605242600. This is the L4 aggregator entry-point — the new
LangGraph node that sits between ``evaluate`` and ``commit`` in R2+.
In R0 (this file), the node is registered but NOT wired into
``graph.py``; activation is gated on Council attestation matching
the L5 routing-around cell pattern from CLAUDE.md row 35.

Gates applied per round (ADR-2605242600 §1):

  G4  ES256 signature must verify against the contributor DID's
      resolved passkey-derived key material.
  G6  Re-run ``charter_rider.scan()`` on ``datasetShardCid`` contents;
      contributor self-attestation is not trusted.
  G7  Contributor DID must be present in the Adherent SBT registry.
  G8  Wellbecoming: discard deltas with lossAfter >= lossBefore * 0.98.
  G9  Byzantine: N >= 5 -> coordinate-wise median (default) or Krum;
      N < 5 -> FedAvg + DP-Gaussian sigma >= 0.01 * ||mean(Delta)||.
  G10 Round-freeze: drop deltas whose baseModelCid != round_base.

R0 contract: the function is a **dry-run only** planner. It accepts
the LangGraph state, scans for any deltas the dispatcher has already
collected into ``state["pending_deltas"]``, applies cheap precondition
checks, and writes a plan summary into ``state["notes"]``. It NEVER
writes ``distilled-models.jsonl``, NEVER mutates the bf16 master,
NEVER signs anything, NEVER deletes IPFS content.

Real merge math (median / Krum / FedAvg + DP) lands in R2 under a
separate ADR with empirical defaults calibrated from the R1 PoC.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ..state import DistillState


# Round-freeze + Wellbecoming defaults. Calibrated per ADR-2605242600 §1.
WELLBECOMING_LOSS_RATIO = 0.98
"""Reject any delta whose lossAfter >= lossBefore * 0.98 (G8)."""

BYZANTINE_MIN_N = 5
"""Switch from FedAvg to coordinate-wise median when accepted N >= 5 (G9)."""

DP_NOISE_SIGMA_FLOOR = 0.01
"""Gaussian sigma floor as a fraction of ||mean(Delta)|| for N < 5 rounds (G9)."""


def federated_aggregate(state: DistillState) -> DistillState:
    """Dry-run planner for the federated aggregation round.

    Reads ``state["pending_deltas"]`` (a list of dicts shaped like the
    ``com.etzhayyim.baien.distributedTrainDelta`` record) if the
    dispatcher has populated it. Otherwise emits an empty-plan note
    and returns.

    Never raises. Failures are recorded in ``state["notes"]`` as
    structured ``[fed-agg]`` lines for operator review.
    """
    notes = state.setdefault("notes", [])
    notes.append("[fed-agg] R0 scaffold — dry-run only; no master mutation")

    if state.get("dry_run") is False:
        notes.append(
            "[fed-agg] dry_run flag is False but R0 aggregator stays in "
            "dry-run regardless (ADR-2605242600 gate: Council attestation pending)"
        )

    pending: list[dict[str, Any]] = list(state.get("pending_deltas", []) or [])
    iteration = state.get("iter", 0)
    base_model_cid = state.get("round_base_model_cid")

    if not pending:
        notes.append(f"[fed-agg] iter={iteration} no pending deltas; plan = noop")
        return state

    survivors: list[dict[str, Any]] = []
    rejections: list[tuple[str, str]] = []

    for d in pending:
        actor_did = d.get("actorDid", "<unknown>")
        if base_model_cid and d.get("baseModelCid") != base_model_cid:
            rejections.append((actor_did, "round-base-mismatch (G10)"))
            continue
        loss_before = d.get("lossBefore")
        loss_after = d.get("lossAfter")
        if loss_before is None or loss_after is None:
            rejections.append((actor_did, "missing-loss-fields"))
            continue
        if loss_after >= loss_before * WELLBECOMING_LOSS_RATIO:
            rejections.append((actor_did, "wellbecoming-regression (G8)"))
            continue
        if not d.get("scannerPass", False):
            rejections.append((actor_did, "self-reported-scanner-fail (G6)"))
            continue
        survivors.append(d)

    if survivors:
        n = len(survivors)
        strategy = "coordinate-median" if n >= BYZANTINE_MIN_N else "fedavg+dp-gaussian"
        notes.append(
            f"[fed-agg] iter={iteration} survivors={n} planned-strategy={strategy} "
            f"sigma-floor={DP_NOISE_SIGMA_FLOOR}"
        )
    else:
        notes.append(f"[fed-agg] iter={iteration} survivors=0 plan = abort-round")

    for actor_did, reason in rejections:
        notes.append(f"[fed-agg] reject did={actor_did} reason={reason}")

    state["federated_plan"] = {
        "iter": iteration,
        "base_model_cid": base_model_cid,
        "received": len(pending),
        "survivors": len(survivors),
        "rejected": [{"did": a, "reason": r} for a, r in rejections],
        "strategy": (
            "coordinate-median"
            if len(survivors) >= BYZANTINE_MIN_N
            else ("fedavg+dp-gaussian" if survivors else "abort-round")
        ),
        "planned_at": datetime.now(timezone.utc).isoformat(),
        "activation_gate": "council-attestation-pending (ADR-2605242600 R2)",
    }
    return state
