"""graph.py — hakken LangGraph graphs.

Two graph variants:
  discovery_graph:       full pipeline (trend_scan → … → social_announce)
  phase_promotion_graph: cron — kotoba Datalog Rule2/3 でフェーズ昇格
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from lg_hakken.nodes.gap_analysis import gap_analysis
from lg_hakken.nodes.import_order import import_order
from lg_hakken.nodes.okaimono_dropship import okaimono_dropship
from lg_hakken.nodes.okaimono_register import okaimono_register
from lg_hakken.nodes.phase_promotion import phase_promotion
from lg_hakken.nodes.phase_router import phase_router, route_by_phase
from lg_hakken.nodes.quality_eval import quality_eval
from lg_hakken.nodes.social_announce import social_announce
from lg_hakken.nodes.supplier_search import supplier_search
from lg_hakken.nodes.trend_scan import trend_scan
from lg_hakken.nodes.tsukuru_order import tsukuru_order
from lg_hakken.state import HakkenState

# ---------------------------------------------------------------------------
# discovery_graph — full SKU discovery + registration pipeline
# ---------------------------------------------------------------------------

_discovery = StateGraph(HakkenState)
_discovery.add_node("trend_scan",        trend_scan)
_discovery.add_node("gap_analysis",      gap_analysis)
_discovery.add_node("supplier_search",   supplier_search)
_discovery.add_node("quality_eval",      quality_eval)
_discovery.add_node("phase_router",      phase_router)
_discovery.add_node("okaimono_dropship", okaimono_dropship)
_discovery.add_node("import_order",      import_order)
_discovery.add_node("tsukuru_order",     tsukuru_order)
_discovery.add_node("okaimono_register", okaimono_register)
_discovery.add_node("social_announce",   social_announce)

_discovery.add_edge(START,            "trend_scan")
_discovery.add_edge("trend_scan",     "gap_analysis")
_discovery.add_edge("gap_analysis",   "supplier_search")
_discovery.add_edge("supplier_search","quality_eval")
_discovery.add_edge("quality_eval",   "phase_router")

_discovery.add_conditional_edges(
    "phase_router",
    route_by_phase,
    {
        "dropship": "okaimono_dropship",
        "import":   "import_order",
        "oem":      "tsukuru_order",
        "end":      END,
    },
)

for _dest in ("okaimono_dropship", "import_order", "tsukuru_order"):
    _discovery.add_edge(_dest, "okaimono_register")

_discovery.add_edge("okaimono_register", "social_announce")
_discovery.add_edge("social_announce",   END)

discovery_graph = _discovery.compile()
"""Compiled discovery pipeline. Run daily via k8s CronJob per category."""

# ---------------------------------------------------------------------------
# phase_promotion_graph — cron: kotoba Datalog で Ph1→Ph2 / Ph2→Ph3 昇格
# ---------------------------------------------------------------------------

_promotion = StateGraph(HakkenState)
_promotion.add_node("phase_promotion", phase_promotion)
_promotion.add_edge(START, "phase_promotion")
_promotion.add_edge("phase_promotion", END)

phase_promotion_graph = _promotion.compile()
"""Compiled phase promotion cron. Run hourly to detect promotion-ready SKUs."""
