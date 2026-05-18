"""uhl_right_neural Pregel topology — 16-vertex StateGraph.

Authoritative per ADR-2605181000 §16-vertex Pregel topology.

P0 (charter Phase 0 — V01-V06 + V10a + V12 + V13 + V16):
  - V01 phenotype             — implemented (actors/phenotype.py)
  - V02 genetic_screen        — implemented (actors/genetic_screen.py)
  - V03 imaging               — implemented (actors/imaging.py)
  - V04 electrophys           — implemented (actors/electrophys.py)
  - V05 cmv_torch             — implemented (actors/cmv_torch.py)
  - V06 substrate_classifier  — implemented (actors/substrate_classifier.py)
  - V10 conventional_device   — implemented (actors/conventional_device.py)
                                (V10a eCI fitting; V10b optoCI is P3)
  - V12 plasticity            — implemented (actors/plasticity.py)
  - V13 outcome (Bayesian)    — implemented (actors/outcome.py)
  - V16 institution_match     — implemented (actors/institution_matcher.py)

Stubs awaiting later phases:
  - V07 OTOF-tx, V11 ABI, V15 reg          → P1
  - V08 BDNF/NT-3                          → P2
  - V09 reprogramming, V10b optoCI         → P3
  - V14 trial_design                       → P1-P2
"""
from __future__ import annotations

from typing import Any, Optional

from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

from .actors.cmv_torch import CmvTorchActor
from .actors.conventional_device import ConventionalDeviceActor
from .actors.electrophys import ElectrophysActor
from .actors.genetic_screen import GeneticScreenActor
from .actors.imaging import ImagingActor
from .actors.institution_matcher import InstitutionMatcherActor
from .actors.outcome import OutcomeActor
from .actors.phenotype import PhenotypeActor
from .actors.plasticity import PlasticityActor
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
    imaging_input: dict[str, Any]       # V03 input
    electrophys_input: dict[str, Any]   # V04 input
    cmv_torch_input: dict[str, Any]     # V05 input
    genetic_result: dict[str, Any]      # V02 output
    imaging_result: dict[str, Any]      # V03 output
    electrophys_result: dict[str, Any]  # V04 output
    cmv_torch_result: dict[str, Any]    # V05 output

    # V06 output
    substrate_decision: dict[str, Any]

    # V07-V11 (stubs for P0)
    otof_tx_plan: dict[str, Any]                   # V07
    neurotrophin_plan: dict[str, Any]              # V08
    reprogramming_plan: dict[str, Any]             # V09
    device_plan: dict[str, Any]                    # V10 (eCI / optoCI)
    abi_plan: dict[str, Any]                       # V11

    # V13 input (P0 — optional)
    outcome_input: dict[str, Any]

    # V12-V15 outputs (V12 + V13 implemented in P0; V14/V15 stubs)
    plasticity_plan: dict[str, Any]                # V12
    outcome_posterior: dict[str, Any]              # V13
    trial_protocol: dict[str, Any]                 # V14 (stub)
    regulatory_path: dict[str, Any]                # V15 (stub)

    # V16 output
    institution_match: dict[str, Any]

    # Cross-cutting
    requires_human_review: bool
    error: str


# ── Vertex implementations ───────────────────────────────────────────────────

_phenotype = PhenotypeActor()
_genetic = GeneticScreenActor()
_imaging = ImagingActor()
_electrophys = ElectrophysActor()
_cmv_torch = CmvTorchActor()
_substrate = SubstrateClassifierActor()
_device = ConventionalDeviceActor()
_plasticity = PlasticityActor()
_outcome = OutcomeActor()
_institutions = InstitutionMatcherActor()


def _v01_phenotype(state: UhlState) -> dict[str, Any]:
    return _phenotype.compute(state)


def _v02_genetic(state: UhlState) -> dict[str, Any]:
    return _genetic.compute(state)


def _v03_imaging(state: UhlState) -> dict[str, Any]:
    return _imaging.compute(state)


def _v04_electrophys(state: UhlState) -> dict[str, Any]:
    return _electrophys.compute(state)


def _v05_cmv_torch(state: UhlState) -> dict[str, Any]:
    return _cmv_torch.compute(state)


def _v06_substrate(state: UhlState) -> dict[str, Any]:
    return _substrate.compute(state)


def _v10_device_fitting(state: UhlState) -> dict[str, Any]:
    return _device.compute(state)


def _v12_plasticity(state: UhlState) -> dict[str, Any]:
    return _plasticity.compute(state)


def _v13_outcome(state: UhlState) -> dict[str, Any]:
    return _outcome.compute(state)


def _v16_institution_match(state: UhlState) -> dict[str, Any]:
    return _institutions.compute(state)


def _make_stub(vertex_id: str, output_key: str) -> Any:
    """Build a no-op stub vertex. Sets `<output_key>` to a marker dict."""

    def _stub(state: UhlState) -> dict[str, Any]:  # noqa: ARG001
        return {output_key: {"_stub": True, "_vertex": vertex_id}}

    _stub.__name__ = f"stub_{vertex_id.lower()}"
    return _stub


# Stubs for treatment-arm vertices not in P0 (charter P1-P3).
_v07_stub = _make_stub("V07_otof_tx", "otof_tx_plan")          # P1
_v08_stub = _make_stub("V08_neurotrophin", "neurotrophin_plan")  # P2
_v09_stub = _make_stub("V09_reprogramming", "reprogramming_plan")  # P3
_v11_stub = _make_stub("V11_abi", "abi_plan")                   # P1

# Trial design + regulatory (P1-P2).
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
    g.add_node("V03_imaging", _v03_imaging)
    g.add_node("V04_electrophys", _v04_electrophys)
    g.add_node("V05_cmv_torch", _v05_cmv_torch)
    g.add_node("V06_substrate_classifier", _v06_substrate)
    g.add_node("V07_otof_tx", _v07_stub)
    g.add_node("V08_neurotrophin", _v08_stub)
    g.add_node("V09_reprogramming", _v09_stub)
    g.add_node("V10_device_fitting", _v10_device_fitting)
    g.add_node("V11_abi", _v11_stub)
    g.add_node("V12_plasticity", _v12_plasticity)
    g.add_node("V13_outcome", _v13_outcome)
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
