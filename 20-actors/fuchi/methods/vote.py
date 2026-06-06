"""vote.py — 扶持 (fuchi) R1(b): real 1 SBT = 1 vote with a 48h timelock.

Per ADR-2606052300 R1. Replaces analyze.py's R0 `yes > no` shortcut with a real ballot tally:

  - **1 SBT = 1 vote** — each member DID casts exactly ONE ballot (a second ballot from the same
    DID is rejected at cast time); every ballot has `weight == 1` (no token-weighted plutocracy).
  - **no-server-key** — a `:server` voter is unrepresentable; ballots are member-signed (G9).
  - **48h timelock** — a tally cannot be FINALIZED before `opened_at + timelock_h` elapses; a
    ballot cast outside the window is not counted.
  - **quorum** — a minimum number of participating ballots is required, else the allocation is
    rejected for want of quorum (it is never auto-accepted on a thin vote).

`tally(...)` returns the full state (including `finalizable` + a `pending` outcome before the
window closes); `finalize(...)` is the strict variant that RAISES if called early.

Stdlib only. Time is an integer hour stamp (passed in; the script clock is unavailable by design).
"""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_TIMELOCK_H = 48
DEFAULT_QUORUM = 3
CHOICES = ("yes", "no", "abstain")


@dataclass(frozen=True)
class Ballot:
    voter_did: str
    choice: str
    cast_at: int                  # hour stamp
    weight: int = 1               # 1 SBT = 1 vote — always 1
    server_held_key: bool = False

    def __post_init__(self) -> None:
        if self.weight != 1:
            raise ValueError("1 SBT = 1 vote INVARIANT: ballot weight must be 1")
        if self.server_held_key:
            raise ValueError("no-server-key INVARIANT (G9): a ballot is member-signed")
        v = self.voter_did.lower()
        if v.startswith(("server", "did:server", ":server")) or v in ("server", "anon"):
            raise ValueError("G9/G4: a :server / :anon voter is unrepresentable")
        if _kw(self.choice) not in CHOICES:
            raise ValueError(f"ballot choice {self.choice!r} not in {CHOICES}")


def _kw(v) -> str:
    return str(v or "").lstrip(":").split("/")[-1].lower()


def cast(ballots: list[Ballot], ballot: Ballot) -> list[Ballot]:
    """Append a ballot, enforcing 1 SBT = 1 vote (a duplicate voter DID is rejected)."""
    if any(b.voter_did == ballot.voter_did for b in ballots):
        raise ValueError(f"1 SBT = 1 vote: {ballot.voter_did} has already voted")
    return [*ballots, ballot]


def ballots_from_seed(records: list[dict]) -> list[Ballot]:
    """Build ballots from seed maps; rejects duplicate voters (1 SBT = 1 vote)."""
    out: list[Ballot] = []
    for r in records:
        out = cast(out, Ballot(
            voter_did=r.get(":ballot/voter", r.get("voter", "?")),
            choice=_kw(r.get(":ballot/choice", r.get("choice", "yes"))),
            cast_at=int(r.get(":ballot/cast-at", r.get("cast_at", 0))),
        ))
    return out


def tally(
    ballots: list[Ballot],
    opened_at: int,
    now: int,
    timelock_h: int = DEFAULT_TIMELOCK_H,
    quorum: int = DEFAULT_QUORUM,
) -> dict:
    """Tally a vote. Only ballots cast within [opened_at, opened_at+timelock_h] count.

    Outcome:
      - pending   if the timelock window has not yet elapsed (now < close);
      - rejected  if quorum (yes+no participating) is not met;
      - accepted  if finalizable, quorum met, and yes > no;
      - rejected  otherwise.
    """
    close = opened_at + timelock_h
    in_window = [b for b in ballots if opened_at <= b.cast_at <= close]
    yes = sum(1 for b in in_window if _kw(b.choice) == "yes")
    no = sum(1 for b in in_window if _kw(b.choice) == "no")
    abstain = sum(1 for b in in_window if _kw(b.choice) == "abstain")
    participating = yes + no
    finalizable = now >= close
    quorum_met = participating >= quorum

    if not finalizable:
        outcome = "pending"
    elif not quorum_met:
        outcome = "rejected"          # never auto-accept on a thin vote
    elif yes > no:
        outcome = "accepted"
    else:
        outcome = "rejected"

    return {
        "yes": yes, "no": no, "abstain": abstain, "voters": len(in_window),
        "opened_at": opened_at, "close": close, "now": now, "timelock_h": timelock_h,
        "quorum": quorum, "quorum_met": quorum_met, "finalizable": finalizable,
        "outcome": outcome,
    }


def finalize(
    ballots: list[Ballot],
    opened_at: int,
    now: int,
    timelock_h: int = DEFAULT_TIMELOCK_H,
    quorum: int = DEFAULT_QUORUM,
) -> dict:
    """Strict finalize — RAISES if the 48h timelock has not elapsed (no early close)."""
    if now < opened_at + timelock_h:
        raise ValueError(
            f"timelock INVARIANT: cannot finalize before {opened_at + timelock_h}h "
            f"(now={now}h, window={timelock_h}h)"
        )
    return tally(ballots, opened_at, now, timelock_h, quorum)
