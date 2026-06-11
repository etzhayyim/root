"""Tests for kamado decommission_robot hot-zone purge + entry loop.

    cd 20-actors/kamado/methods
    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_decommission_robot.py
"""

from __future__ import annotations

import pytest

from _substrate import SafetyError
from decommission_robot import (
    BENZENE_ENTRY_PPM,
    H2S_ENTRY_PPM,
    plan_cut_entry,
    purge_to_entry,
    to_datoms,
)

WITNESS = [
    "did:web:etzhayyim.com:kuniumi:robot:kamado-arm-01",
    "did:web:etzhayyim.com:kuniumi:robot:kamado-mimi-01",
]


# ── purge loop: drives hazardous gas below the entry limit ───────────────────

def test_purge_converges_below_h2s_entry_limit():
    res = purge_to_entry(gas="H2S", target_ppm=H2S_ENTRY_PPM)
    assert res.entry_permitted is True
    assert res.final_ppm <= H2S_ENTRY_PPM + 1e-6
    assert res.final_ppm < res.initial_ppm
    assert res.settling_seconds > 0
    assert res.representative is True


def test_purge_converges_below_benzene_entry_limit():
    res = purge_to_entry(gas="benzene", target_ppm=BENZENE_ENTRY_PPM, initial_ppm=80.0)
    assert res.entry_permitted is True
    assert res.final_ppm <= BENZENE_ENTRY_PPM + 1e-6


def test_purge_too_weak_to_beat_leak_does_not_permit_entry():
    # A purge flow too small to overcome the residual ingress can never hold the
    # zone below the limit — entry must NOT be permitted.
    res = purge_to_entry(
        gas="H2S", target_ppm=H2S_ENTRY_PPM, max_flow=1.0, leak=2.0, k_purge=0.2
    )
    assert res.entry_permitted is False
    assert res.final_ppm > H2S_ENTRY_PPM


# ── entry gate: the safety crux ──────────────────────────────────────────────

def test_entry_refused_when_concentration_above_limit():
    # Robot must NOT enter an un-purged zone — structural SafetyError, not a warning.
    with pytest.raises(SafetyError, match="ENTRY REFUSED"):
        plan_cut_entry(
            target_xy=(1.5, 0.4),
            final_ppm=50.0,
            gas_limit=H2S_ENTRY_PPM,
            member_sig="m:ed25519:demo",
            witness_sigs=WITNESS,
        )


def test_cut_plan_reachable_and_safe_when_purged():
    plan = plan_cut_entry(
        target_xy=(1.5, 0.4),
        final_ppm=8.0,            # below the 10 ppm entry limit
        gas_limit=H2S_ENTRY_PPM,
        member_sig="m:ed25519:demo",
        witness_sigs=WITNESS,
    )
    assert plan["entryPermitted"] is True
    assert plan["reachable"] is True
    assert plan["envelopeOk"] is True
    assert plan["witnessOk"] is True
    assert plan["serverHeldKey"] is False
    assert plan["dryRun"] is True
    # G9: freed hot-zone worker routes to the Basic-High-Income cohort.
    assert plan["displacementCohortRef"].startswith("bhi:")


# ── structural gates ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("use", ["weapon", "fire-control", "mining"])
def test_non_civilian_use_refused_on_purge(use):
    with pytest.raises(SafetyError):
        purge_to_entry(gas="H2S", target_ppm=H2S_ENTRY_PPM, use=use)


@pytest.mark.parametrize("use", ["restart-fossil", "expand", "throughput-revamp"])
def test_fossil_life_extension_use_refused(use):
    # G3: a fossil life-extension verb is not in the civilian allowlist; closed-world
    # refusal rejects it before any motion is planned.
    with pytest.raises(SafetyError):
        plan_cut_entry(
            target_xy=(1.5, 0.4),
            final_ppm=8.0,
            gas_limit=H2S_ENTRY_PPM,
            member_sig="m:sig",
            witness_sigs=WITNESS,
            use=use,
        )


def test_server_signature_refused():
    # G5/G7: a platform-held signature is a structural violation. The zone is purged
    # (final_ppm below limit) so the entry gate passes and we reach the key gate.
    with pytest.raises(SafetyError):
        plan_cut_entry(
            target_xy=(1.5, 0.4),
            final_ppm=8.0,
            gas_limit=H2S_ENTRY_PPM,
            member_sig="m:sig",
            witness_sigs=WITNESS,
            server_sig="s:sig",
        )


def test_missing_member_signature_refused():
    with pytest.raises(SafetyError):
        plan_cut_entry(
            target_xy=(1.5, 0.4),
            final_ppm=8.0,
            gas_limit=H2S_ENTRY_PPM,
            member_sig="",
            witness_sigs=WITNESS,
        )


def test_witness_below_quorum_recorded_not_raised():
    # G8 quorum miss is a Council-escalation record, not a raise (mirrors hikari).
    plan = plan_cut_entry(
        target_xy=(1.5, 0.4),
        final_ppm=8.0,
        gas_limit=H2S_ENTRY_PPM,
        member_sig="m:sig",
        witness_sigs=["did:r:only-one"],
    )
    assert plan["witnessOk"] is False
    assert plan["escalateCouncilLv6"] is True


# ── datoms projection ────────────────────────────────────────────────────────

def test_datoms_are_aggregate_and_dry_run():
    purge = purge_to_entry(gas="H2S", target_ppm=H2S_ENTRY_PPM)
    plan = plan_cut_entry(
        target_xy=(1.5, 0.4),
        final_ppm=purge.final_ppm,
        gas_limit=H2S_ENTRY_PPM,
        member_sig="m:sig",
        witness_sigs=WITNESS,
    )
    d = to_datoms(purge, plan, job_id="decom-001", refinery="rf.jp.muroran")
    assert d[":decommission/dry-run"] is True
    assert d[":decommission/server-held-key"] is False
    assert d[":decommission/entry-permitted"] is True
    assert d[":decommission/representative"] is True
    assert d[":decommission/displacement-cohort-ref"].startswith("bhi:")
