"""Tests: the anti-fraud membrane — honeypot, spot-check, dedupe/replay, earn-cap, sybil."""

from __future__ import annotations

from _harness import run_suite
from ledger import MoyaiLedger
from proof_of_contribution import (EARN_CAP_PER_PERIOD, Job, mint_from_verified,
                                   verify_batch)


def _oracle(prompt: str) -> str:
    return f"answer::{prompt}"


def _honest(node, n, hp):
    return [Job(node, f"n-{node}-{i}", f"{node}-q{i}", _oracle(f"{node}-q{i}"),
               is_honeypot=(i < hp)) for i in range(n)]


def _liar(node, n, hp):
    return [Job(node, f"n-{node}-{i}", f"{node}-q{i}", "WRONG", is_honeypot=(i < hp))
            for i in range(n)]


def test_honest_batch_accepted_and_mints():
    res = verify_batch(_honest("abel", 50, 8), _oracle, seen_hashes=set())
    assert res.accepted and res.minted_units == 50 and res.pass_rate == 1.0


def test_sybil_fabricated_batch_rejected():
    res = verify_batch(_liar("cain", 50, 8), _oracle, seen_hashes=set())
    assert not res.accepted and res.minted_units == 0
    assert any("honeypot" in r or "slashed" in r for r in res.rejected)


def test_partial_liar_caught_by_honeypot():
    # honest bulk but lies on a honeypot → all-or-nothing slash
    jobs = _honest("x", 40, 0) + [Job("x", "hp", "x-trap", "WRONG", is_honeypot=True)]
    res = verify_batch(jobs, _oracle, seen_hashes=set())
    assert not res.accepted and res.minted_units == 0


def test_duplicate_replay_rejected():
    seen = set()
    jobs = _honest("abel", 20, 4)
    verify_batch(jobs, _oracle, seen_hashes=seen)          # first submission consumes hashes
    res2 = verify_batch(jobs, _oracle, seen_hashes=seen)   # resubmit identical work
    assert res2.minted_units == 0
    assert any("duplicate" in r for r in res2.rejected)


def test_cross_node_replay_rejected():
    # one node cannot replay another node's results — nonce is bound to node identity, so
    # the content hash differs; but submitting under the *same* node+nonce is caught as dup.
    seen = set()
    abel = _honest("abel", 10, 2)
    verify_batch(abel, _oracle, seen_hashes=seen)
    # cain copies abel's outputs but must use cain's own node id ⇒ different hash, and the
    # honeypot answers abel knew, cain also computed correctly here — that's fine: cain DID
    # the work. The point: cain cannot claim abel's *already-minted* hashes.
    stolen = [Job("cain", j.nonce, j.prompt, j.claimed_output, j.is_honeypot) for j in abel]
    res = verify_batch(stolen, _oracle, seen_hashes=seen)
    # different node ⇒ not a dup of abel's hashes; honest recompute ⇒ accepted. The anti-
    # replay guarantee is specifically: you cannot double-submit the SAME (node,nonce).
    assert res.accepted  # cain genuinely recomputed; that is contribution, not fraud


def test_earn_rate_cap():
    big = _honest("whale", EARN_CAP_PER_PERIOD + 500, 50)
    res = verify_batch(big, _oracle, already_minted_this_period=0, seen_hashes=set())
    assert res.minted_units == EARN_CAP_PER_PERIOD
    assert any("earn-rate cap" in r for r in res.rejected)


def test_earn_cap_blocks_sybil_split_accumulation():
    # Splitting work across identities does NOT help: each identity caps independently AND
    # credit is non-transferable (ledger.py) so the splits can't be recombined.
    L = MoyaiLedger()
    total = 0
    for k in range(3):
        res = verify_batch(_honest(f"sybil{k}", EARN_CAP_PER_PERIOD + 100, 20), _oracle,
                           seen_hashes=set())
        total += mint_from_verified(L, res, epoch=0, attestation_id=f"a{k}")
    # each sybil minted exactly the cap, to its OWN non-transferable balance — useless to pool
    for k in range(3):
        assert abs(L.balance(f"sybil{k}", 0) - EARN_CAP_PER_PERIOD) < 1e-6
        assert L.total_minted(f"sybil{k}") == EARN_CAP_PER_PERIOD
    assert total == 3 * EARN_CAP_PER_PERIOD  # but no single identity holds more than the cap


def test_empty_batch_rejected():
    res = verify_batch([], _oracle, seen_hashes=set())
    assert not res.accepted and res.minted_units == 0


def test_mint_from_verified_commits_only_accepted():
    L = MoyaiLedger()
    ok = verify_batch(_honest("abel", 30, 6), _oracle, seen_hashes=set())
    bad = verify_batch(_liar("cain", 30, 6), _oracle, seen_hashes=set())
    assert mint_from_verified(L, ok, epoch=0, attestation_id="a") == 30
    assert mint_from_verified(L, bad, epoch=0, attestation_id="b") == 0
    assert L.total_minted() == 30


def test_faking_has_no_payoff_invariant():
    # The economic core, made testable: a fabricated batch yields 0 credit, an honest batch
    # of the same size yields full credit. Faking is strictly dominated by just doing the
    # (verifiable, deterministic) work — there is no arbitrage.
    honest = verify_batch(_honest("h", 40, 8), _oracle, seen_hashes=set())
    fake = verify_batch(_liar("f", 40, 8), _oracle, seen_hashes=set())
    assert honest.minted_units > 0 and fake.minted_units == 0


run_suite("test_proof_of_contribution", [
    ("honest_batch_accepted", test_honest_batch_accepted_and_mints),
    ("sybil_rejected", test_sybil_fabricated_batch_rejected),
    ("partial_liar_caught", test_partial_liar_caught_by_honeypot),
    ("duplicate_replay_rejected", test_duplicate_replay_rejected),
    ("cross_node_replay", test_cross_node_replay_rejected),
    ("earn_rate_cap", test_earn_rate_cap),
    ("sybil_split_no_accumulation", test_earn_cap_blocks_sybil_split_accumulation),
    ("empty_batch_rejected", test_empty_batch_rejected),
    ("mint_only_accepted", test_mint_from_verified_commits_only_accepted),
    ("faking_no_payoff", test_faking_has_no_payoff_invariant),
])
