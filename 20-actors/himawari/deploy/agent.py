"""himawari 向日葵 — solar-PV manufacturing langgraph actor (kotoba WASM cell).

ADR-2606021200. Build entrypoint: compiles to a kotoba-node WASM Component via
``componentize-py`` and runs in-WASM on a live kotoba node (`:8077`) through
invoke.run / the `kotoba_wasm_run` MCP tool. The file MUST be named ``agent.py``
(the build target is the module basename) and MUST expose ``WitWorld.run``.

This is the *deploy-side* graph: it composes the seven manufacturing-chain cells
already implemented under ``himawari/cells/`` (R0.1 — 88 pure-logic tests green,
no RuntimeError stubs) into one ordered StateGraph so the whole chain can be
invoked as a single WASM component. The chain mirrors the manifest:

    supply_procurement (調達) ─feedstock─┐
                                         ▼
    polysilicon_refine → ingot_wafer → cell_process → module_assembly
                                                            │
                                                            ▼
                                                     panel_loading (積込)
                                                            │
                                                            ▼
                                                     outbound_logistics (輸送) → hikari

One advisory ``narrate`` node routes a one-line manufacturing-run summary through
``KotobaLLM`` (kotoba:kais/llm WIT import). On a live host the host binds that
import to the Murakumo fleet (LiteLLM 127.0.0.1:4000) — Charter "Murakumo-only
inference" invariant (ADR-2605215000); leave ``model_cid=""`` so the host's
``MURAKUMO_DEFAULT_MODEL`` selects the deployed model. The narration is advisory:
it never changes the deterministic attestations that ``module_assembly`` /
``outbound_logistics`` emit (G11 deterministic yield + provenance).

The cells write their records back to the kotoba Datom log via their own
``datalog.transact`` host binding (G6/G8 — canonical EAVT state). In local dev
(no host binding) the cells compute the records but do not persist — never a fake
write, never a non-kotoba store (substrate boundary). NO RuntimeError stubs are
introduced here.

Build:
    PATH="$PWD/../../.venv/bin:$PATH" \
      KOTOBA_SITE_PKG="$PWD/../../20-actors" \
      ./scripts/build-pywasm.sh ../../20-actors/himawari/deploy/agent.py
Deploy (in-WASM on the running :8077 node — see deploy/README.md for the exact call):
    kotoba_wasm_run / invoke.run with the produced agent.wasm
"""

from __future__ import annotations

from typing import Any, TypedDict

import wit_world

from kotoba_langgraph import (
    StateGraph,
    KotobaLLM,
    KotobaCheckpointer,
    START,
    END,
    handle_invoke,
)

# componentize-py static analysis does not follow the lazy
# `from kotoba_langgraph._cbor import loads` inside _entry.handle_invoke, nor the
# lazy `from wit_world.imports import llm` inside kotoba_langgraph.llm._wit_infer.
# Pull all three to module scope so they are bundled into the component (otherwise
# it compiles but traps at call time with ModuleNotFoundError). Mirrors the
# aria / okaimono deploy agents (ADR-2605301625 / 2606012100 follow-up).
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401
import wit_world.imports.llm  # noqa: F401

# The seven manufacturing-chain cells (already implemented under himawari/cells/).
# componentize-py needs the cell classes at module scope to bundle them; we import
# the concrete class from each cell module by name (NOT wildcard) so the static
# analyser bundles exactly the right symbols. These imports require the
# `20-actors/` directory on the Python path at build time (KOTOBA_SITE_PKG, see
# the build line in the docstring + deploy.sh).
from himawari.cells.supply_procurement.cell import SupplyProcurementCell  # noqa: F401
from himawari.cells.polysilicon_refine.cell import PolysiliconRefineCell  # noqa: F401
from himawari.cells.ingot_wafer.cell import IngotWaferCell  # noqa: F401
from himawari.cells.cell_process.cell import CellProcessCell  # noqa: F401
from himawari.cells.module_assembly.cell import ModuleAssemblyCell  # noqa: F401
from himawari.cells.panel_loading.cell import PanelLoadingCell  # noqa: F401
from himawari.cells.outbound_logistics.cell import OutboundLogisticsCell  # noqa: F401


# ── State ──────────────────────────────────────────────────────────────────

class HimawariState(TypedDict, total=False):
    # invocation context (one manufacturing run)
    context: dict
    # per-cell outputs, accumulated as the chain advances
    procurement: dict
    polysilicon: dict
    wafer: dict
    cell: dict
    module: dict
    loading: dict
    outbound: dict
    # chain trace + advisory narration
    chain_trace: list
    narrative: str
    narrate_error: str


# Ordered manufacturing chain (manifest order). Each entry is
# (state_key, cell_class, context_subkey) — the cell class is the concrete class
# imported above so we never re-implement a cell here.
_CHAIN = [
    ("procurement", SupplyProcurementCell, "procurement"),
    ("polysilicon", PolysiliconRefineCell, "polysilicon"),
    ("wafer", IngotWaferCell, "wafer"),
    ("cell", CellProcessCell, "cell"),
    ("module", ModuleAssemblyCell, "module"),
    ("loading", PanelLoadingCell, "loading"),
    ("outbound", OutboundLogisticsCell, "outbound"),
]


# ── LLM (routed through kotoba:kais/llm WIT → Murakumo; G5 Murakumo-only) ────

# model_cid="" → host MURAKUMO_DEFAULT_MODEL. Charter requires all religious-corp
# inference go through the Murakumo fleet; the WASM component embeds NO model and
# NO network client — it only emits the llm.infer import.
_llm = KotobaLLM(
    model_cid="",
    system_prompt=(
        "You are himawari, a terse PV-manufacturing-run narrator. Given the "
        "per-stage outcomes of one solar-module manufacturing chain, state in one "
        "sentence what was produced and any gate that refused or binned. No preamble."
    ),
)


# ── Chain runner node ────────────────────────────────────────────────────────

def _run_cell(cell_cls: type, cell_input: dict) -> dict:
    """Instantiate one himawari cell and run its deterministic `.solve()`.

    The cells are fully implemented (R0.1); a cell that refuses on a gate
    (G2/G11/G12/…) returns a structured ``{"refused": True, "reason": ...}`` which
    we record and carry rather than aborting the chain — the deploy path stays
    observable end-to-end. An unexpected exception is captured as ``error`` so one
    faulting cell never corrupts the whole run trace."""
    try:
        return cell_cls().solve(dict(cell_input))
    except Exception as e:  # noqa: BLE001 — a cell fault must not corrupt the run trace
        return {"error": str(e)[:200]}


def _manufacture(state: HimawariState) -> dict:
    """Run the ordered manufacturing chain, threading each cell's output forward.

    The upstream cell output is merged into the next cell's input so the chain of
    custody (feedstock lot → wafer batch → cell batch → module serial) flows
    naturally; G11 traceability is the cells' own responsibility — this node only
    orders them deterministically and records the per-stage status."""
    ctx = state.get("context", {}) or {}
    carry: dict = {}
    out: dict = {}
    trace: list = []
    for state_key, cell_cls, ctx_subkey in _CHAIN:
        cell_input = {**carry, **(ctx.get(ctx_subkey, {}) or {})}
        result = _run_cell(cell_cls, cell_input)
        out[state_key] = result
        status = (
            "error" if result.get("error")
            else "refused" if result.get("refused")
            else "ok"
        )
        # carry only a clean result forward as the chain of custody
        if status == "ok":
            carry = result
        trace.append({"cell": state_key, "node": cell_cls.__name__, "status": status})
    return {**out, "chain_trace": trace}


def _narrate(state: HimawariState) -> dict:
    """One-line advisory run summary via the Murakumo fleet (G5). Advisory only —
    if host inference is unavailable the deterministic chain output still flows."""
    trace = state.get("chain_trace", []) or []
    prompt = [{
        "role": "user",
        "content": "manufacturing run stages: " + ", ".join(
            f"{t['cell']}={t['status']}" for t in trace
        ),
    }]
    try:
        msg = _llm.invoke(prompt)
        return {"narrative": msg.get("content", "")}
    except Exception as e:  # noqa: BLE001 — narration must never break the actor
        return {"narrative": "", "narrate_error": str(e)[:200]}


# ── Graph ───────────────────────────────────────────────────────────────────

_g = StateGraph(HimawariState)
_g.add_node("manufacture", _manufacture)
_g.add_node("narrate", _narrate)
_g.add_edge(START, "manufacture")
_g.add_edge("manufacture", "narrate")
_g.add_edge("narrate", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())


# ── kotoba-node WIT export (boilerplate, always the same) ────────────────────

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
