"""contributor.py — 朱 (ake) anti-vandalism rate + Wellbecoming trajectory (G9). ADR-2606052100.

G9 has two halves, and the SECOND is the charter-sensitive one:

  1. a per-DID RATE LIMIT over a sliding window (a vandal cannot flood the membrane); and
  2. a Wellbecoming ACCEPTANCE TRAJECTORY — an `as-of` history of accepted/refused outcomes,
     NEVER a punitive score-of-soul (kizashi G8). The defining property: throttling is
     **recoverable** — a contributor who starts proposing well again is un-throttled by their
     own next accepted edit. There is no permanent ban, no minted reputation number, no
     ranking of contributors against each other.

All state is an append-only event list; every helper RETURNS A NEW dict (never mutates) so the
trajectory only ever grows, mirroring the Datom-log discipline of revision.py. Time (`now`,
`as_of`) is passed in — deterministic and testable, no wall-clock.

Stdlib only.
"""

from __future__ import annotations

from typing import Any

# defaults — a window and a flood ceiling; both generous (this throttles vandalism, not zeal)
RATE_WINDOW = 3600          # seconds
RATE_MAX_IN_WINDOW = 20     # proposals per DID per window
THROTTLE_RECENT = 5         # look at the last N outcomes
THROTTLE_REFUSED_RUN = 5    # …throttle only if ALL of the last N were refused (a clear run)

_ACCEPT = "accepted"
_REFUSE = "refused"


def empty() -> dict:
    """A fresh trajectory store: {did -> [event, ...]}, event = {outcome, as_of}."""
    return {}


def record(traj: dict, did: str, outcome: str, as_of: int) -> dict:
    """Append one outcome event for `did`. Returns a NEW dict (append-only, never mutates)."""
    outcome = str(outcome).lstrip(":")
    if outcome not in (_ACCEPT, _REFUSE):
        raise ValueError(f"outcome must be {_ACCEPT!r} or {_REFUSE!r}, not {outcome!r}")
    new = {k: list(v) for k, v in traj.items()}
    new.setdefault(did, []).append({"outcome": outcome, "as_of": int(as_of)})
    return new


def events(traj: dict, did: str) -> list[dict]:
    return sorted(traj.get(did, []), key=lambda e: int(e["as_of"]))


def counts(traj: dict, did: str) -> dict:
    evs = traj.get(did, [])
    acc = sum(1 for e in evs if e["outcome"] == _ACCEPT)
    ref = sum(1 for e in evs if e["outcome"] == _REFUSE)
    return {"accepted": acc, "refused": ref}


def acceptance_rate(traj: dict, did: str) -> float | None:
    c = counts(traj, did)
    total = c["accepted"] + c["refused"]
    return None if total == 0 else round(c["accepted"] / total, 4)


def rate_ok(traj: dict, did: str, now: int,
            window: int = RATE_WINDOW, max_in_window: int = RATE_MAX_IN_WINDOW) -> bool:
    """True if `did` may submit one more proposal at `now` without exceeding the flood ceiling."""
    recent = [e for e in traj.get(did, []) if int(e["as_of"]) > now - window]
    return len(recent) < max_in_window


def is_throttled(traj: dict, did: str,
                 recent: int = THROTTLE_RECENT, refused_run: int = THROTTLE_REFUSED_RUN) -> bool:
    """Throttled ⟺ the last `recent` outcomes exist and are an unbroken run of refusals.

    RECOVERABLE by construction: a single accepted edit anywhere in the recent window breaks the
    run, so a contributor un-throttles themselves by proposing well again. This is a behavioural
    signal, NOT a stored score and NOT permanent (G9 — no score-of-soul).
    """
    evs = events(traj, did)
    if len(evs) < recent:
        return False
    tail = evs[-recent:]
    return len(tail) >= refused_run and all(e["outcome"] == _REFUSE for e in tail)


def trajectory(traj: dict, did: str) -> dict:
    """A Wellbecoming view (as-of), NOT a ranking: counts + rate + current throttle state."""
    return {
        "did": did,
        **counts(traj, did),
        "acceptanceRate": acceptance_rate(traj, did),
        "throttled": is_throttled(traj, did),
        "events": len(traj.get(did, [])),
    }
