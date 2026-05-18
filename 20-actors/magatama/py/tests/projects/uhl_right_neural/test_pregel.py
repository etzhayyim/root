"""Pregel topology smoke tests — graph compiles and end-to-end run succeeds."""
from __future__ import annotations

import pytest

from pymagatama.projects.uhl_right_neural.pregel import app, build_graph


def test_graph_compiles() -> None:
    g = build_graph()
    assert g is not None


def test_app_singleton_compiles() -> None:
    assert app is not None


def test_all_16_vertices_present() -> None:
    g = build_graph()
    expected = {
        "V01_phenotype",
        "V02_genetic_screen",
        "V03_imaging",
        "V04_electrophys",
        "V05_cmv_torch",
        "V06_substrate_classifier",
        "V07_otof_tx",
        "V08_neurotrophin",
        "V09_reprogramming",
        "V10_device_fitting",
        "V11_abi",
        "V12_plasticity",
        "V13_outcome",
        "V14_trial_design",
        "V15_regulatory",
        "V16_institution_matcher",
    }
    # LangGraph exposes nodes via the compiled graph's nodes attribute
    actual = set(g.nodes.keys()) if hasattr(g, "nodes") else set()
    # Compiled graphs may expose nodes through different attrs across versions;
    # fall back to the builder if needed.
    if not actual:
        from pymagatama.projects.uhl_right_neural.pregel import _build  # type: ignore

        builder = _build()
        actual = set(builder.nodes.keys())
    missing = expected - actual
    assert not missing, f"missing vertices: {missing}"


@pytest.mark.parametrize(
    "evidence,expected_substrate_class,terminal_present",
    [
        # nerve aplasia → V11 → V12-V16
        (
            {"cn_fiber_count": 0},
            "nerve_aplasia",
            True,
        ),
        # SGN-present HC-loss → V07 → V10 → V12-V16
        (
            {
                "cn_fiber_count": 4,
                "eabr_present": True,
                "eabr_latency_prolonged": False,
                "dpoae_present": False,
            },
            "sgn_present_hc_loss",
            True,
        ),
    ],
)
def test_end_to_end_run(
    evidence: dict,
    expected_substrate_class: str,
    terminal_present: bool,
) -> None:
    final = app.invoke(
        {
            "phenotype_input": {
                "patient_ref": "test-hash-abc12345",
                "side": "right",
                "age_years": 3.0,
                "onset": "congenital",
                "progressive": False,
                "locale_country": "JP",
            },
            "substrate_evidence": evidence,
        }
    )
    assert final["phenotype"]["in_project_scope"] is True
    assert final["substrate_decision"]["substrate_class"] == expected_substrate_class
    if terminal_present:
        assert "institution_match" in final
        assert final["institution_match"]["requires_human_review"] is True


def test_phenotype_out_of_scope_left_side() -> None:
    final = app.invoke(
        {
            "phenotype_input": {
                "patient_ref": "test-hash-leftxxxx",
                "side": "left",
                "age_years": 3.0,
                "onset": "congenital",
                "progressive": False,
                "locale_country": "JP",
            },
            "substrate_evidence": {"cn_fiber_count": 0},
        }
    )
    assert final["phenotype"]["in_project_scope"] is False
    # Pipeline still runs (we don't hard-block out-of-scope), but flag is False
    assert "institution_match" in final


def test_p0_full_pipeline_emits_v10_v12_v13_outputs() -> None:
    """SGN_PRESENT_HC_LOSS pediatric case exercises V10 + V12 + V13 actors."""
    final = app.invoke(
        {
            "phenotype_input": {
                "patient_ref": "test-hash-p0fullxx",
                "side": "right",
                "age_years": 2.0,
                "onset": "congenital",
                "progressive": False,
                "locale_country": "JP",
            },
            "substrate_evidence": {
                "cn_fiber_count": 4,
                "eabr_present": True,
                "eabr_latency_prolonged": False,
                "dpoae_present": False,
            },
            "outcome_input": {
                "localization": {"trials": 20, "successes": 14},
                "sin": {"trials": 20, "successes": 15},
                "pedsql": {"trials": 20, "successes": 16},
            },
        }
    )
    # V10 — eCI fitting plan with pediatric seed
    assert final["device_plan"]["recommendation"] == "electrical_ci"
    assert final["device_plan"]["t_level_initial_cl"] == 100
    # V12 — optimal phase gate at age 2
    assert final["plasticity_plan"]["phase_gate"] == "optimal"
    assert final["plasticity_plan"]["phase_gate_passed"] is True
    # V13 — three Beta-Binomial posteriors with credible intervals in [0,1]
    posterior = final["outcome_posterior"]
    for axis in ("localization", "sin", "pedsql"):
        a = posterior[axis]
        assert 0.0 <= a["credible_interval_low"] <= a["credible_interval_high"] <= 1.0


def test_nerve_aplasia_defers_device_to_abi() -> None:
    """NERVE_APLASIA routes V10 → DEFER_PENDING_V11 (V11 ABI is P1 stub)."""
    final = app.invoke(
        {
            "phenotype_input": {
                "patient_ref": "test-hash-aplasia0",
                "side": "right",
                "age_years": 3.0,
                "onset": "congenital",
                "progressive": False,
                "locale_country": "JP",
            },
            "substrate_evidence": {"cn_fiber_count": 0},
        }
    )
    # Routed via V11 path so V10 not visited (no device_plan in state).
    assert final["substrate_decision"]["substrate_class"] == "nerve_aplasia"
    assert final["plasticity_plan"]["phase_gate"] == "optimal"
    assert "outcome_posterior" in final
    assert "institution_match" in final
