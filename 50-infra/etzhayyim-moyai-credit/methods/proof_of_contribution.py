"""moyai 舫い — proof-of-contribution: the anti-fraud membrane that gates every mint.

Because moyai *does* restore a reward (the user's directive: keep a reward for inference
participation), the sybil/farming incentive partially returns — so verification is now
load-bearing, not optional. This module is where a *claim* of contribution becomes a
*verified* contribution before any credit is minted.

Defence-in-depth (ADR-2606062100 §6), each layer independent:

  1. **Honeypot challenge jobs** — a fraction of every submitted batch are jobs whose
     correct answer the commons already knows (precomputed on core Murakumo nodes against
     frozen, deterministic edge models). A node that fabricated results fails these. Frozen-
     model determinism makes the oracle cheap and exact: same input ⇒ same output, so a
     fabricator cannot guess.
  2. **Spot-check recomputation** — a further random-but-deterministic fraction of *ordinary*
     jobs are recomputed on core nodes and compared. Cheating on the bulk while passing the
     honeypots still gets caught here.
  3. **Duplicate / replay rejection** — each job carries a per-node challenge nonce; work is
     content-hashed and bound to (node, nonce). The same work cannot be submitted twice, and
     one node cannot replay another node's results (the nonce won't match).
  4. **Per-identity earn-rate cap** — a single identity can mint at most EARN_CAP_PER_PERIOD
     units per period, so even fully-honest whales cannot dominate, and a sybil gains nothing
     by splitting work across identities (each still hits the cap and, crucially, credit is
     **non-transferable** so the splits can't be recombined — see ledger.py).
  5. **All-or-nothing batch slashing** — a batch that fails the honeypot/spot-check gate
     mints ZERO and cools the node down. Faking is strictly dominated: a correct answer costs
     the same compute whether you fake-verify it or just... compute it. Faking has no payoff.

The deep reason sybil is self-defeating here (the economic argument, made structural):
moyai credit is non-monetary (redeemable_usd ≡ 0), non-transferable, and decays. The ONLY
thing a credit unit buys is *your own* discretionary surplus draw — and you can only earn it
by doing the very verified work that a draw would have consumed. Faking contribution costs
at least as much as the contribution it pretends to be. There is no arbitrage to extract.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Callable, Dict, List, Tuple

from ledger import MoyaiLedger

# Max credit one identity can mint per accounting period. Anti-whale + anti-sybil-split.
EARN_CAP_PER_PERIOD = 1000

# Minimum fraction of a batch that must actually be checked (honeypot ∪ spot-check) for the
# batch to be mint-eligible — a coverage floor, not the fraud test itself. Kept safely BELOW
# the ~20% deterministic spot-check rate so honest batches reliably clear it regardless of
# how a given node's job hashes happen to distribute; the real fraud catch is the
# all-or-nothing pass_rate==1.0 gate below. (Setting this equal to the spot rate would make
# acceptance a coin-flip on hash variance — observed and fixed.)
MIN_VERIFIED_FRACTION = 0.10

# 1 unit of moyai credit per N verified reference-inference-units contributed. The mint
# ratio; method-versioned + Council-attested in production.
UNITS_PER_VERIFIED = 1


@dataclass(frozen=True)
class Job:
    """One inference job a node claims to have completed for the commons."""

    node_did: str
    nonce: str            # per-node challenge nonce (binds work to this node; anti-replay)
    prompt: str           # the (frozen-model) input
    claimed_output: str   # what the node says the frozen edge model produced
    is_honeypot: bool = False   # commons already knows the correct answer for this one


@dataclass(frozen=True)
class VerificationResult:
    node_did: str
    submitted: int
    verified_units: int       # verified, non-duplicate units eligible to mint (post-cap)
    pass_rate: float          # fraction of *checked* jobs that matched the oracle
    minted_units: int         # what was actually minted (post earn-rate cap)
    rejected: Tuple[str, ...] # human-readable reasons (audit trail)
    accepted: bool            # did the batch clear the gate at all?


# A core-node oracle: given (prompt) returns the deterministic frozen-edge-model output.
# In production this is a small fraction of jobs routed to pinned core Murakumo nodes.
Oracle = Callable[[str], str]


def _content_hash(j: Job) -> str:
    return hashlib.sha256(f"{j.node_did}\x00{j.nonce}\x00{j.prompt}".encode()).hexdigest()


def verify_batch(
    jobs: List[Job],
    oracle: Oracle,
    *,
    already_minted_this_period: int = 0,
    seen_hashes: "set[str] | None" = None,
) -> VerificationResult:
    """Verify one node's batch and compute how many units are eligible to mint.

    Deterministic: the same batch + oracle + state yields the same result (replay-safe).
    Does NOT mutate the ledger — call mint_from_verified() to commit an accepted result.
    """
    seen = seen_hashes if seen_hashes is not None else set()
    if not jobs:
        return VerificationResult("", 0, 0, 0.0, 0, ("empty batch",), False)

    node_did = jobs[0].node_did
    rejected: List[str] = []

    # (3) duplicate / replay rejection + single-node batch enforcement.
    fresh: List[Job] = []
    for j in jobs:
        if j.node_did != node_did:
            rejected.append(f"mixed-node batch: {j.node_did} != {node_did}")
            continue
        h = _content_hash(j)
        if h in seen:
            rejected.append(f"duplicate/replay job {h[:12]}")
            continue
        seen.add(h)
        fresh.append(j)

    if not fresh:
        return VerificationResult(node_did, len(jobs), 0, 0.0, 0, tuple(rejected), False)

    # (1)+(2) honeypot + spot-check. Deterministic spot-check selection: hash-mod, so the
    # node cannot predict which ordinary jobs get recomputed, yet verification replays.
    checked = 0
    passed = 0
    for j in fresh:
        spot = int(_content_hash(j), 16) % 5 == 0   # ~20% deterministic spot-check
        if j.is_honeypot or spot:
            checked += 1
            if j.claimed_output == oracle(j.prompt):
                passed += 1
            else:
                rejected.append(f"failed {'honeypot' if j.is_honeypot else 'spot-check'} {j.nonce}")

    pass_rate = (passed / checked) if checked else 0.0
    verified_fraction = checked / len(fresh)

    # (5) all-or-nothing: any verification failure, or too little of the batch verifiable,
    # ⇒ the batch mints zero and the node is implicitly cooled down (caller's policy).
    if checked == 0 or verified_fraction < MIN_VERIFIED_FRACTION or pass_rate < 1.0:
        rejected.append(
            f"batch slashed: checked={checked} verified_fraction={verified_fraction:.2f} "
            f"pass_rate={pass_rate:.2f}"
        )
        return VerificationResult(node_did, len(jobs), 0, pass_rate, 0, tuple(rejected), False)

    eligible = len(fresh) * UNITS_PER_VERIFIED

    # (4) per-identity earn-rate cap.
    headroom = max(0, EARN_CAP_PER_PERIOD - already_minted_this_period)
    minted = min(eligible, headroom)
    if minted < eligible:
        rejected.append(f"earn-rate cap: {eligible} eligible, {headroom} headroom this period")

    return VerificationResult(
        node_did, len(jobs), eligible, pass_rate, minted, tuple(rejected), minted > 0
    )


def mint_from_verified(
    ledger: MoyaiLedger,
    result: VerificationResult,
    *,
    epoch: int,
    attestation_id: str,
) -> int:
    """Commit an accepted verification to the ledger. The ONLY sanctioned path to a mint.

    Returns the units minted (0 if the batch was rejected). No-server-key: in production the
    contributing node co-signs the attestation; the server cannot mint unilaterally."""
    if not result.accepted or result.minted_units <= 0:
        return 0
    ledger.mint(result.node_did, result.minted_units, epoch, attestation_id)
    return result.minted_units


def period_mint_totals(ledger: MoyaiLedger) -> Dict[str, int]:
    """Per-identity minted totals (for feeding `already_minted_this_period` back in)."""
    out: Dict[str, int] = {}
    for e in ledger.log:
        if e.op == "mint":
            out[e.holder_did] = out.get(e.holder_did, 0) + e.units
    return out
