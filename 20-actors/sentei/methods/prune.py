"""prune.py — 剪定 (sentei) post-hoc pruning engine (ADR-2606072000).

The Council is the PRUNER (剪定者), not the censor. etzhayyim's organism grows from its root
unstoppably; branches manifest on the append-only Datom log; sentei prunes the overgrown /
charter-violating ones AFTER they manifest, to keep the organism beautiful (美しく保つ).

Everything here is the pure, testable heart. The constitutional model is STRUCTURAL — encoded so
violations are *unrepresentable*, not merely discouraged (the nusa/tazuna/kamado/ake/fuchi pattern):

  G1 no-prior-restraint — `prune()` RAISES on an unmanifested branch. The Council cannot stop a
                          branch before it grows. Prior restraint is unrepresentable.
  G2 append-only        — a prune APPENDS a `:prune/*` datom; it never deletes. The branch's full
                          history survives (非終末論). `apply_log` folds the log to a current state.
  G3 growth-unstoppable — prunes target a NAMED branch only; there is no halt-organism action.
  G4 Transparent Force  — a prune carries no verdict/guilt value (care, not punishment); G7 scan.
  G5 no-server-key      — a prune is Council/member-signed; server_held_key is always False.
  G6 reversible         — every prune has the inverse `regraft`; a mistaken cut heals via as-of.
  G7 care-telos         — a prune MUST cite a Charter basis; no verdict token may appear.

Stdlib only. `at` (ISO time) is a parameter so pruning is deterministic + testable.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

# D5 pruning vocabulary. delete / prior-restraint / halt-organism / verdict are ABSENT by design.
PRUNE_ACTIONS = {"quarantine", "retract", "rollback", "revoke"}
INVERSE_ACTION = "regraft"
# Tokens that would make a prune a punitive verdict — unrepresentable (G4/G7).
_VERDICT_TOKENS = ("guilt", "crime", "verdict", "punish", "違法", "有罪", "犯罪", "制裁", "処罰")
# Council levels: a contested / invariant-adjacent prune needs Lv7+; ordinary Lv6+.
COUNCIL_MIN = 6
COUNCIL_INVARIANT = 7


def _digest(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def assert_no_verdict(basis: str) -> None:
    """G7: a prune is grooming, not punishment — refuse any guilt/verdict token in its basis."""
    low = basis.lower()
    for tok in _VERDICT_TOKENS:
        if tok in low:
            raise ValueError(f"G7 violation: verdict token {tok!r} in a prune basis (剪定 is care, not 制裁)")


def prune(
    branch: dict[str, Any],
    action: str,
    basis: str,
    signer_did: str,
    *,
    at: str,
    council_level: int,
    invariant_adjacent: bool = False,
    contested_vote: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Prune a MANIFESTED branch. Returns an append-only `:prune/*` datom (never deletes).

    Raises (the structural invariants):
      G1 — branch not manifested (prior restraint is impossible).
      G3 — unknown action / a halt/delete attempt.
      G4 — signer is the server (no-server-key).
      G7 — verdict token in basis, or missing basis.
      Council — level below the required floor (Lv6+, or Lv7+ when invariant_adjacent).
    """
    if not branch.get("manifested", False):
        raise ValueError(
            "G1 no-prior-restraint: cannot prune an unmanifested branch — the organism's growth "
            "is never pre-blocked; a branch must grow before it can be pruned"
        )
    if action not in PRUNE_ACTIONS:
        raise ValueError(f"G3: {action!r} is not a prune action (delete/halt/prior-restraint are unrepresentable)")
    if signer_did.startswith("did:web:etzhayyim.com#server") or signer_did == "server":
        raise ValueError("G5 no-server-key: a prune must be Council/member-signed; the server cannot sign")
    if not basis or not basis.strip():
        raise ValueError("G7 care-telos: a prune MUST cite a Charter basis (why this branch is overgrown)")
    assert_no_verdict(basis)
    floor = COUNCIL_INVARIANT if invariant_adjacent else COUNCIL_MIN
    if council_level < floor:
        raise ValueError(f"Transparent-Force: prune needs Council Lv{floor}+, got Lv{council_level}")
    # A contested prune additionally needs 1 SBT = 1 vote to carry (G4).
    if contested_vote is not None:
        yes, no = contested_vote.get("yes", 0), contested_vote.get("no", 0)
        if yes <= no:
            raise ValueError(f"contested prune did not carry the vote ({yes} yes / {no} no)")

    branch_id = branch["id"]
    prune_id = f"prune:{branch_id}:{action}:{_digest(branch_id, action, at)}"
    return {
        "id": prune_id,
        "kind": "prune",
        "branchId": branch_id,
        "action": action,           # ∈ PRUNE_ACTIONS only
        "basis": basis,             # Charter basis, no verdict (G7)
        "signerDid": signer_did,    # Council/member (G5)
        "serverHeldKey": False,     # const False (G5)
        "councilLevel": council_level,
        "invariantAdjacent": invariant_adjacent,
        "at": at,
        "reversible": True,         # G6 — every prune can be regrafted
        "nonAdjudicating": True,    # G7 — no guilt/verdict value
    }


def regraft(prune_datom: dict[str, Any], signer_did: str, *, at: str, basis: str = "restoration") -> dict[str, Any]:
    """G6: the inverse of a prune — un-prune / heal a mistaken cut (append-only, like ake revert)."""
    if prune_datom.get("kind") != "prune":
        raise ValueError("regraft target must be a prune datom")
    assert_no_verdict(basis)
    if signer_did == "server" or signer_did.startswith("did:web:etzhayyim.com#server"):
        raise ValueError("G5 no-server-key: a regraft must be Council/member-signed")
    bid = prune_datom["branchId"]
    return {
        "id": f"regraft:{prune_datom['id']}:{_digest(bid, at)}",
        "kind": "regraft",
        "branchId": bid,
        "prunesId": prune_datom["id"],
        "basis": basis,
        "signerDid": signer_did,
        "serverHeldKey": False,
        "at": at,
    }


def apply_log(events: list[dict[str, Any]], as_of: str | None = None) -> dict[str, str]:
    """Fold the append-only prune/regraft log into the CURRENT pruned-state of each branch.

    Returns {branchId: state} where state ∈ {"live", <prune action>}. With `as_of` (ISO date/time)
    only events at/before that point are folded — 非終末論 time-travel over the pruning history.
    A regraft restores the branch to "live"; the pruned event stays in history (never deleted).
    """
    def visible(ev: dict[str, Any]) -> bool:
        if not as_of:
            return True
        return str(ev.get("at", "")) <= str(as_of) + "T23:59:59.999Z"

    state: dict[str, str] = {}
    for ev in sorted([e for e in events if visible(e)], key=lambda e: str(e.get("at", ""))):
        bid = ev.get("branchId")
        if not bid:
            continue
        if ev.get("kind") == "prune":
            state[bid] = ev["action"]
        elif ev.get("kind") == "regraft":
            state[bid] = "live"
    return state


def to_datoms(event: dict[str, Any]) -> list[dict[str, Any]]:
    """Serialize a prune/regraft event to kotoba EAVT datoms (`:sentei.prune/*`)."""
    e = event["id"]
    ns = ":sentei.prune/" if event["kind"] == "prune" else ":sentei.regraft/"
    out = []
    for k, v in event.items():
        if k == "id":
            continue
        out.append({"e": e, "a": ns + k, "v_edn": json.dumps(v, ensure_ascii=False), "added": True})
    return out


if __name__ == "__main__":
    branch = {"id": "kanae.fundFlowEdge:jp-mext-2024-outlay", "manifested": True}
    p = prune(branch, "quarantine", "G10 named-party disclosure pending review", "did:web:etzhayyim.com:council#5of7",
              at="2026-06-07T20:00:00.000Z", council_level=6)
    print("pruned :", p["action"], "→", apply_log([p]))
    r = regraft(p, "did:web:etzhayyim.com:council#5of7", at="2026-06-08T09:00:00.000Z")
    print("regraft:", apply_log([p, r]))
    print("as-of pre-regraft:", apply_log([p, r], as_of="2026-06-07"))
