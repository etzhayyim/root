"""Tests for the kuni-umi → open-ot commissioning handoff.

    cd 20-actors/kuni-umi/robotics
    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_commissioning.py
"""

from __future__ import annotations

import pytest

from commissioning import (
    commission_microgrid_site,
    run_microgrid_acceptance,
    to_datoms,
)
from safety import SafetyError

LOOPS = [
    "did:web:etzhayyim.com:openot:loop:droop-p-f",
    "did:web:etzhayyim.com:openot:loop:anti-islanding-rocof",
]
WITNESS = ["did:web:etzhayyim.com:kuniumi:robot:otete-01",
           "did:web:etzhayyim.com:kuniumi:robot:mimi-01"]


def test_acceptance_passes_for_normal_load_step():
    a = run_microgrid_acceptance(load_step_kw=140.0)
    assert a["passed"] is True
    assert a["final_freq_hz"] == pytest.approx(50.0, abs=2e-2)
    assert a["rocof_tripped"] is False


def test_acceptance_flags_islanding_scale_step():
    a = run_microgrid_acceptance(load_step_kw=190.0)
    assert a["rocof_tripped"] is True
    assert a["passed"] is False  # ROCOF trip → not a clean commission


def test_full_handoff_marks_site_operational():
    rec = commission_microgrid_site(
        "did:web:etzhayyim.com:kuniumi:site:demo-001",
        loop_dids=LOOPS,
        member_sig="m:ed25519:demo",
        witness_sigs=WITNESS,
        load_step_kw=140.0,
    )
    assert rec.site_state == "operational"
    assert rec.acceptance_passed is True
    assert rec.witness_ok is True
    assert rec.server_held_key is False
    assert rec.dry_run is True
    assert rec.open_ot_loop_dids == tuple(LOOPS)


def test_witness_below_quorum_yields_punch_list():
    rec = commission_microgrid_site(
        "did:web:etzhayyim.com:kuniumi:site:demo-002",
        loop_dids=LOOPS,
        member_sig="m:sig",
        witness_sigs=["did:r:a"],
        load_step_kw=140.0,
    )
    assert rec.site_state == "punch-list"
    assert rec.witness_ok is False
    assert rec.escalate_council_lv6 is True


def test_server_signature_refused():
    with pytest.raises(SafetyError):
        commission_microgrid_site(
            "did:web:etzhayyim.com:kuniumi:site:demo-003",
            loop_dids=LOOPS,
            member_sig="m:sig",
            witness_sigs=WITNESS,
            server_sig="s:sig",
        )


def test_datoms_are_keyless_and_dry_run():
    rec = commission_microgrid_site(
        "did:web:etzhayyim.com:kuniumi:site:demo-004",
        loop_dids=LOOPS, member_sig="m:sig", witness_sigs=WITNESS,
    )
    d = to_datoms(rec)
    assert d[":commission/server-held-key"] is False
    assert d[":commission/dry-run"] is True
    assert d[":commission/site-state"] == "operational"


# ─── R1 device-in-the-loop acceptance tier ───────────────────────────

def _device_evidence(**over):
    base = {
        "freq_restored": True, "rocof_trip": False, "twin_verdict_match": True,
        "dry_run": True, "server_held_key": False,
    }
    base.update(over)
    return base


def test_device_evidence_upgrades_acceptance_tier():
    rec = commission_microgrid_site(
        "did:web:etzhayyim.com:kuniumi:site:demo-r1",
        loop_dids=LOOPS, member_sig="m:sig", witness_sigs=WITNESS,
        device_evidence=_device_evidence(),
    )
    assert rec.acceptance_tier == "device-wasm"
    assert rec.site_state == "operational"
    assert to_datoms(rec)[":commission/acceptance-tier"] == "device-wasm"


def test_inconsistent_device_evidence_demotes_to_punch_list():
    rec = commission_microgrid_site(
        "did:web:etzhayyim.com:kuniumi:site:demo-r1-bad",
        loop_dids=LOOPS, member_sig="m:sig", witness_sigs=WITNESS,
        device_evidence=_device_evidence(rocof_trip=True),
    )
    assert rec.acceptance_tier == "python-twin"
    assert rec.site_state == "punch-list"  # evidence tightens, never loosens


def test_no_device_evidence_stays_python_twin_tier():
    rec = commission_microgrid_site(
        "did:web:etzhayyim.com:kuniumi:site:demo-r0",
        loop_dids=LOOPS, member_sig="m:sig", witness_sigs=WITNESS,
    )
    assert rec.acceptance_tier == "python-twin"
    assert rec.site_state == "operational"
