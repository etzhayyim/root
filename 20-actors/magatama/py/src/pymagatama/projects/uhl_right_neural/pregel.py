"""uhl_right_neural Pregel topology — 16-vertex StateGraph.

Authoritative per ADR-2605181000 §16-vertex Pregel topology.

P0 MVP (this scaffold):
  - V01 phenotype          — implemented (actors/phenotype.py)
  - V06 substrate_classify — implemented (actors/substrate_classifier.py)
  - V16 institution_match  — implemented (actors/institution_matcher.py)
  - V02-V05, V07-V15       — declared as no-op stubs (state pass-through)
                              with `_stub: true` flag for observability

Subsequent phases per the charter's P1-P3 plan will replace each stub with
a real actor without changing the topology.
"""
from __future__ import annotations

from typing import Any, Optional

from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

from .actors.electrophys import ElectrophysActor
from .actors.genetic_screen import GeneticScreenActor
from .actors.institution_matcher import InstitutionMatcherActor
from .actors.phenotype import PhenotypeActor
from .actors.substrate_classifier import SubstrateClass, SubstrateClassifierActor


# ── State ────────────────────────────────────────────────────────────────────


class UhlState(TypedDict, total=False):
    """Pregel state for uhl_right_neural. Shape is intentionally permissive
    (TypedDict total=False) so stub vertices can pass through unchanged."""

    # V01 input
    phenotype_input: dict[str, Any]
    # V01 output
    phenotype: dict[str, Any]

    # V02-V05 evidence fan-in
    substrate_evidence: dict[str, Any]
    genetic_input: dict[str, Any]       # V02 input
    electrophys_input: dict[str, Any]   # V04 input
    genetic_result: dict[str, Any]      # V02 output
    imaging_result: dict[str, Any]      # V03 (stub)
    electrophys_result: dict[str, Any]  # V04 output
    cmv_torch_result: dict[str, Any]    # V05 (stub)

    # V06 output
    substrate_decision: dict[str, Any]

    # V07-V11 (stubs for P0)
    otof_tx_plan: dict[str, Any]                   # V07
    neurotrophin_plan: dict[str, Any]              # V08
    reprogramming_plan: dict[str, Any]             # V09
    device_plan: dict[str, Any]                    # V10 (eCI / optoCI)
    abi_plan: dict[str, Any]                       # V11

    # V12-V15 (stubs for P0)
    plasticity_plan: dict[str, Any]                # V12
    outcome_posterior: dict[str, Any]              # V13
    trial_protocol: dict[str, Any]                 # V14
    regulatory_path: dict[str, Any]                # V15

    # V16 output
    institution_match: dict[str, Any]

    # Cross-cutting
    requires_human_review: bool
    error: str


# ── Vertex implementations ───────────────────────────────────────────────────

_phenotype = PhenotypeActor()
_genetic = GeneticScreenActor()
_electrophys = ElectrophysActor()
_substrate = SubstrateClassifierActor()
_institutions = InstitutionMatcherActor()


def _v01_phenotype(state: UhlState) -> dict[str, Any]:
    return _phenotype.compute(state)


def _v02_genetic(state: UhlState) -> dict[str, Any]:
    return _genetic.compute(state)


def _v04_electrophys(state: UhlState) -> dict[str, Any]:
    return _electrophys.compute(state)


def _v06_substrate(state: UhlState) -> dict[str, Any]:
    return _substrate.compute(state)


def _v16_institution_match(state: UhlState) -> dict[str, Any]:
    return _institutions.compute(state)


def _make_stub(vertex_id: str, output_key: str) -> Any:
    """Build a no-op stub vertex. Sets `<output_key>` to a marker dict."""

    def _stub(state: UhlState) -> dict[str, Any]:  # noqa: ARG001
        return {output_key: {"_stub": True, "_vertex": vertex_id}}

    _stub.__name__ = f"stub_{vertex_id.lower()}"
    return _stub


# Stubs for V03 + V05. V02 + V04 are real actors (see imports above).
_v03_stub = _make_stub("V03_imaging", "imaging_result")
_v05_stub = _make_stub("V05_cmv_torch", "cmv_torch_result")

# Stubs for treatment-arm vertices (V07-V11). Selected based on V06 decision.
_v07_stub = _make_stub("V07_otof_tx", "otof_tx_plan")
_v08_stub = _make_stub("V08_neurotrophin", "neurotrophin_plan")
_v09_stub = _make_stub("V09_reprogramming", "reprogramming_plan")
_v10_stub = _make_stub("V10_device_fitting", "device_plan")
_v11_stub = _make_stub("V11_abi", "abi_plan")

# Stubs for the downstream chain V12-V15.
_v12_stub = _make_stub("V12_plasticity", "plasticity_plan")
_v13_stub = _make_stub("V13_outcome", "outcome_posterior")
_v14_stub = _make_stub("V14_trial_design", "trial_protocol")
_v15_stub = _make_stub("V15_regulatory", "regulatory_path")


# ── Routing ──────────────────────────────────────────────────────────────────


def _route_after_substrate(state: UhlState) -> str:
    """Conditional branch after V06 — pick first downstream treatment vertex.

    The full V07-V11 fan-out is conceptual; in this scaffold we route to a
    single representative vertex per substrate class, and the rest of the
    chain (V12-V16) runs sequentially. P1 will introduce true parallel
    treatment-arm fan-out.
    """
    decision = state.get("substrate_decision") or {}
    klass_raw = decision.get("substrate_class")
    if not klass_raw:
        return "V10_device_fitting"  # safe default
    klass = SubstrateClass(klass_raw)

    if klass is SubstrateClass.NERVE_APLASIA:
        return "V11_abi"
    if klass is SubstrateClass.SGN_ABSENT_NERVE_PRESENT:
        return "V09_reprogramming"
    if klass is SubstrateClass.SGN_DEGENERATING_NERVE_PRESENT:
        return "V08_neurotrophin"
    if klass is SubstrateClass.SGN_PRESENT_HC_LOSS:
        return "V07_otof_tx"
    # INDETERMINATE — go straight to V10 fallback for human review
    return "V10_device_fitting"


# ── Build ────────────────────────────────────────────────────────────────────


def _build() -> StateGraph:
    g = StateGraph(UhlState)

    # Vertices
    g.add_node("V01_phenotype", _v01_phenotype)
    g.add_node("V02_genetic_screen", _v02_genetic)
    g.add_node("V03_imaging", _v03_stub)
    g.add_node("V04_electrophys", _v04_electrophys)
    g.add_node("V05_cmv_torch", _v05_stub)
    g.add_node("V06_substrate_classifier", _v06_substrate)
    g.add_node("V07_otof_tx", _v07_stub)
    g.add_node("V08_neurotrophin", _v08_stub)
    g.add_node("V09_reprogramming", _v09_stub)
    g.add_node("V10_device_fitting", _v10_stub)
    g.add_node("V11_abi", _v11_stub)
    g.add_node("V12_plasticity", _v12_stub)
    g.add_node("V13_outcome", _v13_stub)
    g.add_node("V14_trial_design", _v14_stub)
    g.add_node("V15_regulatory", _v15_stub)
    g.add_node("V16_institution_matcher", _v16_institution_match)

    # S0-S1: V01 → V02-V05 fan-out → V06 fan-in
    g.set_entry_point("V01_phenotype")
    for v in (
        "V02_genetic_screen",
        "V03_imaging",
        "V04_electrophys",
        "V05_cmv_torch",
    ):
        g.add_edge("V01_phenotype", v)
        g.add_edge(v, "V06_substrate_classifier")

    # S2: V06 → treatment branch
    g.add_conditional_edges(
        "V06_substrate_classifier",
        _route_after_substrate,
        {
            "V07_otof_tx": "V07_otof_tx",
            "V08_neurotrophin": "V08_neurotrophin",
            "V09_reprogramming": "V09_reprogramming",
            "V10_device_fitting": "V10_device_fitting",
            "V11_abi": "V11_abi",
        },
    )

    # S3: every treatment branch → V10 device fitting (eCI/optoCI/ABI selection)
    # ABI vertex is its own device path, so it skips V10.
    for v in (
        "V07_otof_tx",
        "V08_neurotrophin",
        "V09_reprogramming",
    ):
        g.add_edge(v, "V10_device_fitting")
    g.add_edge("V10_device_fitting", "V12_plasticity")
    g.add_edge("V11_abi", "V12_plasticity")

    # S4-S7: linear chain V12 → V13 → V14 → V15 → V16 → END
    g.add_edge("V12_plasticity", "V13_outcome")
    g.add_edge("V13_outcome", "V14_trial_design")
    g.add_edge("V14_trial_design", "V15_regulatory")
    g.add_edge("V15_regulatory", "V16_institution_matcher")
    g.add_edge("V16_institution_matcher", END)
    return g


app = _build().compile()


def build_graph() -> Any:
    """Factory entry point for langgraph_loader (py_factory kind)."""
    return _build().compile()


__all__ = ["UhlState", "app", "build_graph"]
