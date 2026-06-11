#!/usr/bin/env python3
"""State-machine tests for 助 (tasuke) cells (R0). .solve() is NOT called (it raises).

Standalone-runnable AND pytest-compatible:
    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_state_machines.py
    python3 test_state_machines.py
"""
from __future__ import annotations

import pathlib
import sys

# methods on path (triage / report_gen / evidence imported by the state machines)
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "methods"))

from intake_triage.cell import IntakeTriageCell
from intake_triage.state_machine import IntakePhase, transition_to_screened, transition_to_triaged
from evidence_preservation.cell import EvidencePreservationCell
from evidence_preservation.state_machine import EvidencePhase, preserve
from police_report.cell import PoliceReportCell
from police_report.state_machine import ReportPhase, generate as gen_report
from platform_abuse.cell import PlatformAbuseCell
from platform_abuse.state_machine import RequestPhase, generate as gen_request
from account_recovery.cell import AccountRecoveryCell
from account_recovery.state_machine import RecoveryPhase, plan as gen_plan

_CASE = {":case/id": "c1", ":case/subject": "did:web:etzhayyim.com:member:alice",
         ":case/scam-kind": ":unauthorized-transfer", ":case/loss-jpy": 480000,
         ":case/narrative": "不正送金"}


# ── intake_triage (G1/G4/G7) ─────────────────────────────────────────────────
def _screen(**over):
    base = {"cell_state": {}, "case_id": "c1", "subject": "did:member:alice",
            "consent": True, "support_cost_jpy": 0, "server_held_key": False}
    base.update(over)
    return transition_to_screened(base)


def test_intake_screens_and_triages():
    cs = _screen()["cell_state"]
    assert cs["phase"] == IntakePhase.SCREENED.value
    cs2 = transition_to_triaged({"cell_state": cs, "intake": _CASE})["cell_state"]
    assert cs2["phase"] == IntakePhase.TRIAGED.value
    assert cs2["payload"]["scamKind"] == "unauthorized-transfer"
    assert cs2["payload"]["supportCostJpy"] == 0


def test_intake_refuses_no_consent():
    cs = _screen(consent=False)["cell_state"]
    assert cs["phase"] == IntakePhase.REFUSED.value and "G7" in cs["refusal"]


def test_intake_refuses_nonzero_cost():
    cs = _screen(support_cost_jpy=500)["cell_state"]
    assert cs["phase"] == IntakePhase.REFUSED.value and "G1" in cs["refusal"]


def test_intake_refuses_server_held_key():
    cs = _screen(server_held_key=True)["cell_state"]
    assert cs["phase"] == IntakePhase.REFUSED.value and "no-server-key" in cs["refusal"]


# ── evidence_preservation (G6) ───────────────────────────────────────────────
def test_evidence_preserves_clean_items():
    items = [{":evidence/id": "e1", ":evidence/case": "c1", ":evidence/kind": ":screenshot",
              ":evidence/envelope-ref": "ipfs://bafyX", ":evidence/bytes": "abc",
              ":evidence/captured-at": 1}]
    cs = preserve({"cell_state": {}, "case_id": "c1", "items": items})["cell_state"]
    assert cs["phase"] == EvidencePhase.PRESERVED.value and cs["count"] == 1


def test_evidence_refuses_plaintext_pii():
    items = [{":evidence/id": "e1", ":evidence/kind": ":screenshot",
              ":evidence/envelope-ref": "ipfs://x", ":evidence/plaintext": "secret"}]
    cs = preserve({"cell_state": {}, "case_id": "c1", "items": items})["cell_state"]
    assert cs["phase"] == EvidencePhase.REFUSED.value and "G6" in cs["refusal"]


# ── police_report (G3) ───────────────────────────────────────────────────────
def test_report_generates_member_authored():
    cs = gen_report({"cell_state": {}, "case_id": "c1", "kind": "damage-report",
                     "authored_by": "member", "case": _CASE})["cell_state"]
    assert cs["phase"] == ReportPhase.GENERATED.value
    assert cs["payload"]["authoredBy"] == "member" and cs["payload"]["published"] is False


def test_report_refuses_police_authored():
    cs = gen_report({"cell_state": {}, "case_id": "c1", "kind": "damage-report",
                     "authored_by": "police", "case": _CASE})["cell_state"]
    assert cs["phase"] == ReportPhase.REFUSED.value and "G3" in cs["refusal"]


# ── platform_abuse (bank/platform request) ───────────────────────────────────
def test_request_generates_bank_freeze():
    cs = gen_request({"cell_state": {}, "case_id": "c1", "kind": "bank-freeze-request",
                      "authored_by": "member", "case": _CASE})["cell_state"]
    assert cs["phase"] == RequestPhase.GENERATED.value
    assert cs["payload"]["authoredBy"] == "member"


def test_request_refuses_agent_author():
    cs = gen_request({"cell_state": {}, "case_id": "c1", "kind": "platform-request",
                      "authored_by": "server", "case": _CASE})["cell_state"]
    assert cs["phase"] == RequestPhase.REFUSED.value and "G3" in cs["refusal"]


# ── account_recovery (G2 self-submit) ────────────────────────────────────────
def test_recovery_plans_self_submit():
    cs = gen_plan({"cell_state": {}, "case_id": "c1", "service": "Google",
                   "role": "self-submit", "case": _CASE})["cell_state"]
    assert cs["phase"] == RecoveryPhase.PLANNED.value
    assert cs["payload"]["supportRole"] == ":self-submit" and cs["payload"]["steps"]


def test_recovery_refuses_representation_role():
    cs = gen_plan({"cell_state": {}, "case_id": "c1", "service": "LINE",
                   "role": "represent", "case": _CASE})["cell_state"]
    assert cs["phase"] == RecoveryPhase.REFUSED.value and "G2" in cs["refusal"]


# ── .solve() raises at R0 ────────────────────────────────────────────────────
def test_all_cells_solve_raise():
    for C in (IntakeTriageCell, EvidencePreservationCell, PoliceReportCell,
              PlatformAbuseCell, AccountRecoveryCell):
        try:
            C().solve({})
            assert False, f"{C.__name__}.solve should raise at R0"
        except RuntimeError:
            pass


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL {fn.__name__}: {e}")
    print(f"{len(fns) - failed}/{len(fns)} passed in cells/test_state_machines.py")
    sys.exit(1 if failed else 0)
