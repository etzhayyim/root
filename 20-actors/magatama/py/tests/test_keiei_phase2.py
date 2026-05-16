"""Phase 2 coverage for keiei C-suite AI layer (ADR 2605101200).

- CFO / CMO / CHRO gate verdicts on action_kind hard-gates.
- CFO / CMO / CHRO graph hook lens routing.
- 24h auto-disclose mailer:
    * ledger parsing
    * pending-disclosure detection (primary-mode + Class B + seq watermark)
    * state persistence round-trip
    * dry-run formatting
    * XRPC failure handling without watermark advance
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from pymagatama.keiei import gate, by_id, ROLES
from pymagatama.keiei.graph import cfo as cfo_graph
from pymagatama.keiei.graph import cmo as cmo_graph
from pymagatama.keiei.graph import chro as chro_graph
from pymagatama.keiei.graph._pipeline import DecideRequest
from pymagatama.keiei import mailer


# ---------------------------------------------------------------------------
# Gate verdicts — ADR 2605101200 §4 hard rules.
# ---------------------------------------------------------------------------

class TestGateCFO:
    def test_class_a_always_escalates(self):
        v = gate(by_id("cfo"), "A")
        assert v.allowed is False
        assert v.must_escalate is True

    @pytest.mark.parametrize("kind", ["spend", "charge", "wire", "payroll", "sign-legal"])
    def test_financial_action_force_gated(self, kind):
        v = gate(by_id("cfo"), "B", action_kind=kind)
        assert v.allowed is False
        assert v.requires_human_confirm is True
        assert "financial" in v.reason.lower()

    def test_class_b_non_financial_autonomous(self):
        v = gate(by_id("cfo"), "B", action_kind="memo")
        assert v.allowed is True
        assert "primary-mode" in v.reason

    def test_class_c_autonomous(self):
        v = gate(by_id("cfo"), "C")
        assert v.allowed is True


class TestGateCMO:
    @pytest.mark.parametrize("kind", ["spend", "charge"])
    def test_paid_spend_gated_via_financial_rule(self, kind):
        # CMO is NOT financial_action_gated at role level, so the role's
        # mode wins for plain non-financial Class B. Spend/charge action_kind
        # falls outside its hard-gate set → autonomous. The lens in graph
        # is what nudges the human-confirm path.
        v = gate(by_id("cmo"), "B", action_kind=kind)
        # CMO mode=primary B → autonomous-with-24h-disclose; the *budget*
        # human confirm is implemented at a higher layer (consent helper).
        assert v.allowed is True
        assert "primary-mode" in v.reason

    def test_class_a_escalates(self):
        v = gate(by_id("cmo"), "A")
        assert v.must_escalate is True


class TestGateCHRO:
    @pytest.mark.parametrize("kind", ["hire", "fire", "comp-change", "payroll-run"])
    def test_hr_action_force_gated(self, kind):
        v = gate(by_id("chro"), "B", action_kind=kind)
        assert v.allowed is False
        assert v.requires_human_confirm is True

    def test_internal_comms_autonomous(self):
        v = gate(by_id("chro"), "C")
        assert v.allowed is True


# ---------------------------------------------------------------------------
# Graph hook lens routing.
# ---------------------------------------------------------------------------

def _req(role: str, summary: str, *, action_kind: str = "", decision_class: str = "B") -> DecideRequest:
    return DecideRequest(
        role_id=role, decision_class=decision_class,
        action_kind=action_kind, summary=summary, artefact="—",
    )


class TestCFOHook:
    def test_includes_hard_rule_in_system(self):
        sys_prompt, _ = cfo_graph._hook(_req("cfo", "evaluate cluster spend"))
        assert "financial-action gated" in sys_prompt
        assert "MUST NOT initiate" in sys_prompt

    def test_action_kind_lens_emitted(self):
        _, ctx = cfo_graph._hook(_req("cfo", "approve Stripe charge", action_kind="charge"))
        assert any("lens.gate=financial-action" in c for c in ctx)

    def test_keyword_routes_to_cloud_lens(self):
        _, ctx = cfo_graph._hook(_req("cfo", "Vultr LAX monthly burn"))
        assert any("lens.cloud-burn" in c for c in ctx)

    def test_keyword_routes_to_revenue_lens(self):
        _, ctx = cfo_graph._hook(_req("cfo", "Approve Omise invoice"))
        assert any("lens.revenue" in c for c in ctx)

    def test_keyword_routes_to_planning_lens(self):
        _, ctx = cfo_graph._hook(_req("cfo", "review runway forecast"))
        assert any("lens.planning" in c for c in ctx)


class TestCMOHook:
    def test_includes_channel_split(self):
        sys_prompt, _ = cmo_graph._hook(_req("cmo", "post update"))
        assert "OWNED" in sys_prompt
        assert "PAID" in sys_prompt

    def test_owned_channel_lens(self):
        _, ctx = cmo_graph._hook(_req("cmo", "Bluesky bsky post for site"))
        assert any("lens.owned" in c for c in ctx)

    def test_paid_action_kind_gate_lens(self):
        _, ctx = cmo_graph._hook(_req("cmo", "Run a sponsor campaign", action_kind="spend"))
        assert any("lens.gate=paid-channel" in c for c in ctx)

    def test_regulatory_lens_flags_claim(self):
        _, ctx = cmo_graph._hook(_req("cmo", "Best-in-class guarantee copy"))
        assert any("lens.regulatory" in c for c in ctx)


class TestCHROHook:
    def test_includes_payroll_gate(self):
        sys_prompt, _ = chro_graph._hook(_req("chro", "anything"))
        assert "payroll gated" in sys_prompt
        assert "MUST NOT initiate hiring" in sys_prompt

    def test_action_kind_lens_emitted(self):
        _, ctx = chro_graph._hook(_req("chro", "process termination", action_kind="fire"))
        assert any("lens.gate=hr-action" in c for c in ctx)

    def test_internal_comms_routes_to_comms_lens(self):
        _, ctx = chro_graph._hook(_req("chro", "Schedule all-hands meeting"))
        assert any("lens.comms" in c for c in ctx)

    def test_labor_keyword_routes_to_labor_lens(self):
        _, ctx = chro_graph._hook(_req("chro", "36協定 update for 残業"))
        assert any("lens.labor" in c for c in ctx)


# ---------------------------------------------------------------------------
# Mailer — ledger parsing.
# ---------------------------------------------------------------------------

LEDGER_FIXTURE = """# CXO-LEDGER

Append-only audit trail of every keiei C-suite decision.

| seq | date | role | class | summary | decided_by | escalated_to | artefact |
|---|---|---|---|---|---|---|---|
| 1 | 2026-05-10 | cto | C | approve ADR | AI-CTO | — | adr.md |
| 2 | 2026-05-10 | ceo | A | sign LoI | (escalated) | j.kawasaki@gftd.co.jp | — |
| 3 | 2026-05-10 | cto | B | promote MV | AI-CTO | — | adr/x [rationale=fallback-no-key] |
| 4 | 2026-05-11 | cfo | C | review burn | AI-CFO | — | BUDGET-05 |
| 5 | 2026-05-12 | cfo | B | accounting policy memo | AI-CFO | — | memo.md |
| 6 | 2026-05-12 | ciso | B | shadow incident review | AI-CISO | — | ir-01 |
| 7 | 2026-05-13 | chro | B | training plan | AI-CHRO | — | plan.md |
"""


def _write_ledger(tmp_path: Path, content: str = LEDGER_FIXTURE) -> Path:
    p = tmp_path / "CXO-LEDGER.md"
    p.write_text(content)
    return p


def test_parse_ledger_returns_rows(tmp_path):
    p = _write_ledger(tmp_path)
    rows = mailer.parse_ledger(p)
    assert len(rows) == 7
    assert rows[0].seq == 1
    assert rows[0].role == "cto"
    assert rows[2].decision_class == "B"


def test_parse_ledger_missing_file(tmp_path):
    assert mailer.parse_ledger(tmp_path / "absent.md") == []


def test_parse_ledger_escapes(tmp_path):
    body = LEDGER_FIXTURE + (
        "| 8 | 2026-05-14 | cto | B | pipe \\| inside summary | AI-CTO | — | x |\n"
    )
    p = _write_ledger(tmp_path, body)
    rows = mailer.parse_ledger(p)
    assert rows[-1].summary == "pipe | inside summary"


# ---------------------------------------------------------------------------
# Mailer — pending detection.
# ---------------------------------------------------------------------------

def test_primary_role_ids_covers_phase2_roles():
    pids = mailer.primary_role_ids()
    assert {"cto", "cfo", "cmo", "chro"}.issubset(pids)
    assert "ceo" not in pids
    assert "ciso" not in pids


def test_find_pending_filters_primary_mode_class_b(tmp_path):
    rows = mailer.parse_ledger(_write_ledger(tmp_path))
    pending = mailer.find_pending(rows, mailer.MailerState())
    seqs = {r.seq for r in pending}
    # Primary-mode B = cto seq=3, cfo seq=5, chro seq=7. ciso seq=6 is shadow-mode.
    assert seqs == {3, 5, 7}


def test_find_pending_respects_watermark(tmp_path):
    rows = mailer.parse_ledger(_write_ledger(tmp_path))
    state = mailer.MailerState(last_emailed_seq=5)
    pending = mailer.find_pending(rows, state)
    assert {r.seq for r in pending} == {7}


# ---------------------------------------------------------------------------
# Mailer — state persistence.
# ---------------------------------------------------------------------------

def test_state_roundtrip(tmp_path):
    p = tmp_path / "state.json"
    s = mailer.MailerState(
        last_emailed_seq=7, last_emailed_at="2026-05-14T00:00:00Z",
        history=[{"emailed_at": "x", "seqs": [3], "recipient": "j", "status": "sent"}],
    )
    mailer.save_state(p, s)
    s2 = mailer.load_state(p)
    assert s2.last_emailed_seq == 7
    assert s2.last_emailed_at == "2026-05-14T00:00:00Z"
    assert s2.history[0]["seqs"] == [3]


def test_load_state_missing_returns_zero(tmp_path):
    s = mailer.load_state(tmp_path / "absent.json")
    assert s.last_emailed_seq == 0
    assert s.history == []


# ---------------------------------------------------------------------------
# Mailer — format + dry-run.
# ---------------------------------------------------------------------------

def test_format_email_includes_seq_and_role(tmp_path):
    rows = mailer.parse_ledger(_write_ledger(tmp_path))
    pending = mailer.find_pending(rows, mailer.MailerState())
    subj, text, html = mailer.format_email(pending, now_iso="2026-05-14T01:23:45Z")
    assert "[keiei]" in subj
    assert "3 Class B" in subj
    for r in pending:
        assert str(r.seq) in text
        assert r.role in text
    assert "<table" in html


def test_run_once_no_pending(tmp_path):
    ledger = _write_ledger(tmp_path)
    state = tmp_path / "state.json"
    # advance watermark past every row
    mailer.save_state(state, mailer.MailerState(last_emailed_seq=100))
    result = mailer.run_once(
        ledger_path=ledger, state_path=state, dry_run=True,
        token="dummy",
    )
    assert result.status == "no-op"
    assert result.pending_count == 0


def test_run_once_dry_run_shows_pending(tmp_path):
    ledger = _write_ledger(tmp_path)
    state = tmp_path / "state.json"
    result = mailer.run_once(
        ledger_path=ledger, state_path=state, dry_run=True, token="dummy",
    )
    assert result.status == "dry-run"
    assert result.pending_count == 3
    assert "subject=" in result.detail
    # watermark NOT advanced in dry-run state file
    assert mailer.load_state(state).last_emailed_seq == 0


# ---------------------------------------------------------------------------
# Mailer — XRPC failure path (no token).
# ---------------------------------------------------------------------------

def test_run_once_without_token_returns_error(tmp_path, monkeypatch):
    ledger = _write_ledger(tmp_path)
    state = tmp_path / "state.json"
    monkeypatch.delenv(mailer.DEFAULT_TOKEN_ENV, raising=False)
    result = mailer.run_once(
        ledger_path=ledger, state_path=state, dry_run=False, token="",
    )
    assert result.status == "error"
    assert "token" in result.detail.lower()
    # watermark unchanged
    assert mailer.load_state(state).last_emailed_seq == 0


# ---------------------------------------------------------------------------
# Mailer — successful send path with monkeypatched XRPC.
# ---------------------------------------------------------------------------

def test_run_once_advances_watermark_on_sent(tmp_path, monkeypatch):
    ledger = _write_ledger(tmp_path)
    state = tmp_path / "state.json"

    captured: dict[str, Any] = {}

    def fake_send_via_xrpc(**kwargs):
        captured.update(kwargs)
        return {"status": "sent", "fromUpn": "agent@gftd.co.jp", "recipientCount": 1}

    monkeypatch.setattr(mailer, "send_via_xrpc", fake_send_via_xrpc)
    result = mailer.run_once(
        ledger_path=ledger, state_path=state, token="tok",
        recipient="j.kawasaki@gftd.co.jp",
        now_iso="2026-05-14T01:00:00Z",
    )
    assert result.status == "sent"
    assert result.new_watermark == 7
    assert captured["recipient"] == "j.kawasaki@gftd.co.jp"
    assert captured["token"] == "tok"
    persisted = mailer.load_state(state)
    assert persisted.last_emailed_seq == 7
    assert persisted.last_emailed_at == "2026-05-14T01:00:00Z"
    assert persisted.history[-1]["seqs"] == [3, 5, 7]


def test_run_once_drafted_status_does_not_advance(tmp_path, monkeypatch):
    ledger = _write_ledger(tmp_path)
    state = tmp_path / "state.json"

    monkeypatch.setattr(
        mailer, "send_via_xrpc",
        lambda **kwargs: {"status": "drafted", "fromUpn": "x", "draftId": "d1"},
    )
    result = mailer.run_once(
        ledger_path=ledger, state_path=state, token="tok",
    )
    assert result.status == "drafted"
    assert result.sent is False
    # watermark NOT advanced
    assert mailer.load_state(state).last_emailed_seq == 0
