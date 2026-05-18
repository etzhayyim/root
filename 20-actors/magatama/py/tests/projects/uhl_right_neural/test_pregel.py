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
