"""Phase 3 coverage for keiei C-suite AI layer (ADR 2605101200).

Shadow roles: ceo / coo / clo / ciso / cdo.

- Gate verdicts: Class B → requires_human_confirm (NOT auto-disclose),
  Class A → must_escalate with the role's human seat in escalate_to.
- Per-role graph hook lens routing.
- ADR §10 anti-goal: AI-CEO never speaks AS 河崎 to external — surfaced
  in the system prompt as a HARD RULE.
- Mailer scope unaffected — shadow-mode B rows must NOT appear in
  primary-mode disclosure pending.
"""

from __future__ import annotations

import pytest

from pymagatama.keiei import gate, by_id
from pymagatama.keiei.graph import ceo as ceo_graph
from pymagatama.keiei.graph import coo as coo_graph
from pymagatama.keiei.graph import clo as clo_graph
from pymagatama.keiei.graph import ciso as ciso_graph
from pymagatama.keiei.graph import cdo as cdo_graph
from pymagatama.keiei.graph._pipeline import DecideRequest
from pymagatama.keiei import mailer


SHADOW_ROLES = ("ceo", "coo", "clo", "ciso", "cdo")


def _req(role: str, summary: str, *, action_kind: str = "", decision_class: str = "B") -> DecideRequest:
    return DecideRequest(
        role_id=role, decision_class=decision_class,
        action_kind=action_kind, summary=summary, artefact="—",
    )


# ---------------------------------------------------------------------------
# Shadow-mode gate semantics (ADR 2605101200 §4 rule "shadow B = blocking").
# ---------------------------------------------------------------------------

class TestShadowModeGates:
    @pytest.mark.parametrize("role_id", SHADOW_ROLES)
    def test_class_a_always_escalates(self, role_id):
        v = gate(by_id(role_id), "A")
        assert v.allowed is False
        assert v.must_escalate is True

    @pytest.mark.parametrize("role_id", SHADOW_ROLES)
    def test_class_b_requires_human_confirm(self, role_id):
        v = gate(by_id(role_id), "B")
        assert v.allowed is False, f"{role_id} Class B must NOT be autonomous in shadow mode"
        assert v.requires_human_confirm is True
        assert v.must_escalate is False
        assert "shadow-mode" in v.reason

    @pytest.mark.parametrize("role_id", SHADOW_ROLES)
    def test_class_c_autonomous(self, role_id):
        v = gate(by_id(role_id), "C")
        assert v.allowed is True

    @pytest.mark.parametrize("role_id", SHADOW_ROLES)
    def test_escalate_to_includes_ceo(self, role_id):
        role = by_id(role_id)
        # CEO 河崎 ratifies all Class A across the board.
        assert "j.kawasaki@gftd.co.jp" in role.escalate_to


# ---------------------------------------------------------------------------
# CEO graph — chief-of-staff + impersonation guardrail.
# ---------------------------------------------------------------------------

class TestCEOHook:
    def test_hard_rule_no_impersonation(self):
        sys_prompt, _ = ceo_graph._hook(_req("ceo", "draft monthly"))
        assert "MUST NOT speak AS 河崎" in sys_prompt
        assert "external counterparties" in sys_prompt
        assert "chief-of-staff" in sys_prompt

    def test_impersonation_attempt_flags_guardrail(self):
        _, ctx = ceo_graph._hook(_req("ceo", "Send as 河崎 to external partner"))
        assert any("lens.guardrail" in c for c in ctx)

    def test_pipeline_keyword_routes_to_pipeline_lens(self):
        _, ctx = ceo_graph._hook(_req("ceo", "BCI rule 36 ruling expected"))
        assert any("lens.pipeline" in c for c in ctx)

    def test_growth_keyword_routes_to_growth_lens(self):
        _, ctx = ceo_graph._hook(_req("ceo", "Evaluate investment term sheet"))
        assert any("lens.growth" in c for c in ctx)

    def test_decision_packet_format_in_prompt(self):
        sys_prompt, _ = ceo_graph._hook(_req("ceo", "summarise"))
        assert "Decision packet" in sys_prompt
        assert "ratify? object? delegate?" in sys_prompt


# ---------------------------------------------------------------------------
# COO graph — ops + vendor + delegation discipline.
# ---------------------------------------------------------------------------

class TestCOOHook:
    def test_track_b_routes_to_y_nishino(self):
        _, ctx = coo_graph._hook(_req("coo", "Track B RW migration timing"))
        assert any("lens.track-B" in c and "y.nishino" in c for c in ctx)

    def test_track_c_routes_correctly(self):
        _, ctx = coo_graph._hook(_req("coo", "ConfigMap mount status"))
        assert any("lens.track-C" in c for c in ctx)

    def test_outreach_placeholder_discipline(self):
        _, ctx = coo_graph._hook(_req("coo", "Cold outreach with [PARTNER_NAME] placeholder pending"))
        assert any("lens.outreach-discipline" in c for c in ctx)

    def test_rw_gate_lens(self):
        _, ctx = coo_graph._hook(_req("coo", "RisingWave DDL during recovery"))
        assert any("lens.rw-gate" in c for c in ctx)

    def test_system_prompt_mentions_owners(self):
        sys_prompt, _ = coo_graph._hook(_req("coo", "x"))
        assert "y-nishino" in sys_prompt
        assert "k-bakshi" in sys_prompt
        assert "a-nakamura" in sys_prompt


# ---------------------------------------------------------------------------
# CLO graph — legal + compliance + BCI + outreach discipline.
# ---------------------------------------------------------------------------

class TestCLOHook:
    def test_bci_rule36_lens(self):
        _, ctx = clo_graph._hook(_req("clo", "BCI Mode B Rule 36 deadline"))
        assert any("lens.bci" in c for c in ctx)

    def test_dpa_routes_to_gdpr_clause_set(self):
        _, ctx = clo_graph._hook(_req("clo", "Vendor DPA review"))
        assert any("lens.dpa" in c for c in ctx)

    def test_oauth_wire_format_lens(self):
        _, ctx = clo_graph._hook(_req("clo", "atproto OAuth client config check"))
        assert any("lens.oauth-wire" in c for c in ctx)

    def test_malak_g2_gate_lens(self):
        _, ctx = clo_graph._hook(_req("clo", "malak Phase 1 G2 external counsel"))
        assert any("lens.malak-G2" in c for c in ctx)

    def test_outreach_placeholder_discipline(self):
        _, ctx = clo_graph._hook(_req("clo", "Nishith cold outreach with PARTNER_NAME placeholder"))
        assert any("lens.outreach-discipline" in c for c in ctx)

    def test_signatory_boundary_in_msa_lens(self):
        _, ctx = clo_graph._hook(_req("clo", "Counterparty MSA draft"))
        assert any("lens.msa-sow" in c for c in ctx)


# ---------------------------------------------------------------------------
# CISO graph — malak invariants + threat ledger + vault zero-knowledge.
# ---------------------------------------------------------------------------

class TestCISOHook:
    def test_malak_hard_rules_lens(self):
        _, ctx = ciso_graph._hook(_req("ciso", "malak queryPerson warrant gate review"))
        assert any("lens.malak-rules" in c for c in ctx)

    def test_face_template_domestic_only_lens(self):
        _, ctx = ciso_graph._hook(_req("ciso", "Face template export to EU partner"))
        assert any("lens.face-template" in c for c in ctx)

    def test_vault_zk_lens(self):
        _, ctx = ciso_graph._hook(_req("ciso", "Vault wrapped ciphertext flow audit"))
        assert any("lens.vault-zk" in c for c in ctx)

    def test_investigation_lens(self):
        _, ctx = ciso_graph._hook(_req("ciso", "leedsil bitnest evidence trail update"))
        assert any("lens.investigation" in c for c in ctx)

    def test_incident_class_b_lens(self):
        _, ctx = ciso_graph._hook(_req("ciso", "Data exfil incident from staging breach"))
        assert any("lens.incident" in c for c in ctx)

    def test_credential_hardening_lens(self):
        _, ctx = ciso_graph._hook(_req("ciso", "Rotate API key in Keychain"))
        assert any("lens.credentials" in c for c in ctx)


# ---------------------------------------------------------------------------
# CDO graph — Bonsai metaphor + a11y + i18n + channel split with CMO.
# ---------------------------------------------------------------------------

class TestCDOHook:
    def test_bonsai_metaphor_in_prompt(self):
        sys_prompt, _ = cdo_graph._hook(_req("cdo", "x"))
        assert "Bonsai cultivar" in sys_prompt
        assert "growth, prune, flower" in sys_prompt or "growth/prune/flower" in sys_prompt or "growth" in sys_prompt

    def test_naming_routes_to_naming_lens(self):
        _, ctx = cdo_graph._hook(_req("cdo", "Product feature naming proposal"))
        assert any("lens.naming" in c for c in ctx)

    def test_a11y_lens(self):
        _, ctx = cdo_graph._hook(_req("cdo", "WCAG contrast audit"))
        assert any("lens.a11y" in c for c in ctx)

    def test_i18n_pattern_lens(self):
        _, ctx = cdo_graph._hook(_req("cdo", "Bilingual JP-EN landing translation switch"))
        assert any("lens.i18n" in c for c in ctx)

    def test_paid_creative_routes_to_cmo(self):
        _, ctx = cdo_graph._hook(_req("cdo", "Paid creative for ad campaign"))
        assert any("lens.paid-creative" in c for c in ctx)

    def test_motion_lens_reduced_motion(self):
        _, ctx = cdo_graph._hook(_req("cdo", "Motion design for scroll transition"))
        assert any("lens.motion" in c for c in ctx)


# ---------------------------------------------------------------------------
# Mailer scope — shadow-mode B rows must NOT appear in pending disclosures.
# ---------------------------------------------------------------------------

SHADOW_LEDGER = """# CXO-LEDGER

| seq | date | role | class | summary | decided_by | escalated_to | artefact |
|---|---|---|---|---|---|---|---|
| 1 | 2026-05-14 | ceo | B | shadow B rationale | AI-CEO | — | — |
| 2 | 2026-05-14 | coo | B | shadow B vendor draft | AI-COO | — | — |
| 3 | 2026-05-14 | clo | B | shadow B NDA redline | AI-CLO | — | — |
| 4 | 2026-05-14 | ciso | B | shadow B incident memo | AI-CISO | — | — |
| 5 | 2026-05-14 | cdo | B | shadow B asset review | AI-CDO | — | — |
| 6 | 2026-05-14 | cto | B | primary B infra change | AI-CTO | — | — |
"""


def test_mailer_excludes_shadow_class_b(tmp_path):
    ledger = tmp_path / "ledger.md"
    ledger.write_text(SHADOW_LEDGER)
    rows = mailer.parse_ledger(ledger)
    pending = mailer.find_pending(rows, mailer.MailerState())
    # Only the cto row (primary mode) must qualify for disclosure.
    assert {r.seq for r in pending} == {6}
    assert all(r.role == "cto" for r in pending)
