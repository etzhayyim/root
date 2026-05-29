"""pymagatama.organism.junkan — analysis-only societal feedback-loop observer.

ADR-2605290927. junkan performs systems-thinking on society at large: from
passive, public, aggregate data it builds a system-dynamics model (stocks /
flows / reinforcing-R + balancing-B causal loops) and reads off which loops spin
virtuous (好循環) / vicious (悪循環) / neutral / transitioning, plus Meadows
leverage-point candidates.

ANALYSIS-ONLY (G4): there is no dispatch / post / mention / email / transaction
/ actuator anywhere in this package. The only output is a read-only
``FindingBundle`` (``actuation_taken`` const False). Publication beyond Council
is performed by other actors (ossekai / kataribe) under G13 — never by junkan.

Data model: datom / Datalog (immutable society-stock facts + tx-time history).
Reference impl is ``DatomStore``; the canonical production binding is kotoba-kqe
(ADR-2605262130, Datomic-isomorphic EAVT/AEVT/AVET/VAET). Proprietary Datomic is
NOT used (Charter Rider §2(e)+§2(c)).

Status: R1-preparatory pure analysis core (offline, no fleet, no inference, no
network). Fleet cell activation + kotoba-kqe binding + real passive sensors are
Council-gated (Bootstrap Council Seat 2-5 RFP close 2026-06-19).
"""

from __future__ import annotations

from .datom import Datom, DatomStore
from .flows import FlowEdge, infer_flow
from .graph import (
    FindingBundle,
    LoopSpec,
    StockSeries,
    build_junkan_graph,
    run_analysis,
)
from .leverage import (
    MEADOWS_LEVELS,
    LeveragePointCandidate,
    rank_leverage_candidates,
)
from .loops import (
    REGIMES,
    CausalLoop,
    RegimeShift,
    build_loop,
    classify_regime,
    detect_regime_shift,
    loop_polarity,
)
from .stocks import StockObservation, record_stock, trajectory

ADR = "2605290927"

# G4 is enforced by ABSENCE: this package exports no outward-channel callable.
GATES = (
    "G1 charter-rider scan I/O",
    "G2 kotoba attestation lineage",
    "G3 passive-only collection",
    "G4 analysis-only / no actuation (defining; enforced by absence)",
    "G5 no causal overclaim (hypothesis-only)",
    "G6 aggregate-only / no individual modeling",
    "G7 wellbecoming non-eschatological framing",
    "G8 no commercial systems-analysis/BI/intel SaaS",
    "G9 datom immutability (append-only)",
    "G10 murakumo-only inference",
    "G11 no prescription / no prediction-as-fact",
    "G12 open-source model + findings",
    "G13 default council-internal; publication by others",
)

__all__ = [
    "ADR",
    "GATES",
    "Datom",
    "DatomStore",
    "FlowEdge",
    "infer_flow",
    "CausalLoop",
    "RegimeShift",
    "REGIMES",
    "build_loop",
    "classify_regime",
    "detect_regime_shift",
    "loop_polarity",
    "LeveragePointCandidate",
    "MEADOWS_LEVELS",
    "rank_leverage_candidates",
    "StockObservation",
    "record_stock",
    "trajectory",
    "StockSeries",
    "LoopSpec",
    "FindingBundle",
    "run_analysis",
    "build_junkan_graph",
]
