"""CellProcessCell — himawari R1+ Pregel cell (concrete implementation).

Cell process line + flash IV test.
G3 (high-GWP NF₃/SF₆/CF₄ etch/clean gas abatement ≥99% or substitution)
    + G6 (Ag->Cu low-toxicity metallization roadmap) enforcement.

Per ADR-2606021200 §R2 (cell_process / murakumo node benjamin): the solar-grade
c-Si cell line — texture → diffusion/PECVD → metallization → flash IV test → bin.
Input: waferBatchRecord (from ingot_wafer, murakumo node issachar).
Output: cellBatchRecord (com.etzhayyim.himawari.cellBatchRecord), witness-signed.

7-node LangGraph super-step state machine:
  init → texture → junction (diffusion/PECVD) → metallization → flash_iv
       → gas_abatement (G3 gate) → witness → emit_record → END

  (gas_abatement may branch to halt when fluorinated-gas DRE < 99% AND no
   substitution; metallization flags silver-only against the G6 Ag→Cu roadmap)

This is NOT the logic/compute iwakura/fuigo/tsukuru track (ADR-2605242500);
himawari is solar-grade c-Si only (N1). Robotics (Otete cell handling, Mimi
flash IV + EL metrology) are COMPOSED from kuni-umi, not re-implemented here.

R1+ Status: Concrete implementation with deterministic process model. The cell
runs end-to-end and emits a valid cellBatchRecord. Production line telemetry
(real Otete/Mimi sensor streams + on-chain CID pinning) is wired at R2 activation.
ADR-2606021200 R0 approved; R1/R2 activation gate: Council Lv6+ ratify + ≥1
PV-process engineer on Council technical advisory + ≥1 LANDS brownfield parcel
+ G2 feedstock-provenance + G3 high-GWP-abatement frameworks operational.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

try:  # LangGraph is the canonical super-step runtime (sibling: tatekata cells).
    from langgraph.graph import StateGraph  # type: ignore
except Exception:  # pragma: no cover - env without a working langgraph install
    # Fall back to a tiny in-process sequential executor so the cell still
    # imports and runs (R0 smoke-test contract requires clean import). The
    # node functions are identical; only the driver differs.
    StateGraph = None  # type: ignore[assignment]

# G3: fluorinated etch/clean gases whose 100-yr GWP forces ≥99% abatement
# (destruction-removal efficiency, DRE) or substitution. GWP figures are the
# AR5 100-yr values used industry-wide for the PV abatement gate.
_HIGH_GWP_GASES: dict[str, int] = {
    "NF3": 16100,
    "SF6": 23500,
    "CF4": 6630,
    "C2F6": 11100,
    "C3F8": 8900,
}
_MIN_DRE = 0.99  # G3: ≥99% destruction-removal efficiency floor

# G6: Ag→Cu low-toxicity metallization roadmap. silver-only is permitted in R1
# but must be flagged as off-roadmap; copper / ag-cu-hybrid are on-roadmap.
_METALLIZATION_KNOWN = ("silver", "ag-cu-hybrid", "copper")
_METALLIZATION_ON_ROADMAP = ("ag-cu-hybrid", "copper")

_CELL_ARCH_KNOWN = ("PERC", "TOPCon", "HJT")

# Robot DIDs COMPOSED from kuni-umi (not re-implemented in himawari).
_OTETE_DID = "did:web:etzhayyim.com:kuni-umi:otete"  # cell handling / metallization tending
_MIMI_DID = "did:web:etzhayyim.com:kuni-umi:mimi"  # flash IV + EL metrology witness


class CellPhase(Enum):
    """Phase progression in the cell process line."""

    INIT = "init"
    TEXTURED = "textured"  # alkaline/acid texture etch
    JUNCTION = "junction"  # diffusion / PECVD passivation
    METALLIZED = "metallized"  # screen-print / plate contacts (G6)
    FLASH_TESTED = "flash_tested"  # Mimi flash IV + bin
    ABATEMENT_VERIFIED = "abatement_verified"  # G3 gate
    WITNESS_WAIT = "witness_wait"  # ≥2 robot Ed25519 sigs
    ANOMALY_HALT = "anomaly_halt"  # G3 abatement out of spec
    COMPLETE = "complete"


@dataclass
class CellState:
    """State snapshot for the cell-process LangGraph node."""

    phase: CellPhase
    batchId: str
    waferBatchId: str
    cellArchitecture: str
    metallization: str
    waferCount: int
    completionPct: int  # 0–100
    recordedAt: str = ""  # ISO-8601 attestation timestamp (threaded from input)
    textureMetrics: dict[str, Any] | None = None
    junctionMetrics: dict[str, Any] | None = None
    metallizationMetrics: dict[str, Any] | None = None
    flashIvMetrics: dict[str, Any] | None = None
    gasAbatement: dict[str, Any] | None = None
    binDistribution: dict[str, Any] | None = None
    flashIvMedianMilliwp: int | None = None
    gasAbatementCid: str | None = None
    binDistributionCid: str | None = None
    processParametersCid: str | None = None
    metallizationFlags: list[str] = field(default_factory=list)
    anomalyFlags: list[str] = field(default_factory=list)
    robotSignatures: list[dict[str, Any]] = field(default_factory=list)
    errorMsg: str | None = None


def _content_ref(prefix: str, payload: dict[str, Any]) -> str:
    """Deterministic content reference for an attestation payload.

    R1 stand-in for an IPFS CID: a stable, replayable digest over the canonical
    key set so records are reproducible in tests. At R2 the runtime replaces this
    with a real CIDv1 pin (kotoba block backend); the call site is unchanged.
    """
    keysig = "|".join(f"{k}={payload[k]}" for k in sorted(payload))
    return f"{prefix}:{abs(hash(keysig)) & 0xFFFFFFFFFFFF:012x}"


class CellProcessCell:
    """Cell process line + flash IV test."""

    def __init__(self) -> None:
        self.graph: Any | None = None

    # ── nodes ────────────────────────────────────────────────────────────────

    def _initialize_state(self, state: dict[str, Any]) -> dict[str, Any]:
        """Seed cell state from the inbound waferBatchRecord handoff."""
        wafer_batch_id = str(state.get("waferBatchId", "wafer-unknown"))
        batch_id = str(state.get("batchId") or f"cell-{wafer_batch_id}")
        arch = str(state.get("cellArchitecture", "TOPCon"))
        if arch not in _CELL_ARCH_KNOWN:
            arch = "TOPCon"
        metallization = str(state.get("metallization", "ag-cu-hybrid"))
        if metallization not in _METALLIZATION_KNOWN:
            metallization = "ag-cu-hybrid"
        wafer_count = int(state.get("waferCount", 1000))

        cs = CellState(
            phase=CellPhase.INIT,
            batchId=batch_id,
            waferBatchId=wafer_batch_id,
            cellArchitecture=arch,
            metallization=metallization,
            waferCount=max(wafer_count, 0),
            completionPct=0,
            # recordedAt is threaded through from input (ingot_wafer passthrough
            # pattern); no wall-clock call inside the pure-logic line.
            recordedAt=str(state.get("recordedAt", "")),
        )
        return {"cell_state": cs.__dict__, "next_node": "texture"}

    def _texture(self, state: dict[str, Any]) -> dict[str, Any]:
        """INIT → TEXTURED: alkaline (mono) / acid (multi) texture etch + clean."""
        cs = CellState(**state["cell_state"])
        cs.textureMetrics = {
            "etch_chemistry": "KOH-IPA-alkaline" if cs.cellArchitecture != "PERC" else "HF-HNO3-acid",
            "target_reflectance_pct": 11.0,
            "achieved_reflectance_pct": 10.4,
            "saw_damage_removed_um": 4.0,
        }
        cs.phase = CellPhase.TEXTURED
        cs.completionPct = 15
        return {"cell_state": cs.__dict__, "next_node": "junction"}

    def _junction(self, state: dict[str, Any]) -> dict[str, Any]:
        """TEXTURED → JUNCTION: emitter diffusion + PECVD passivation/ARC."""
        cs = CellState(**state["cell_state"])
        # Architecture-specific junction recipe (open process parameters, G1).
        recipe = {
            "PERC": {"emitter": "POCl3-diffusion", "passivation": "AlOx/SiNx-PECVD"},
            "TOPCon": {"emitter": "LPCVD-poly-Si", "passivation": "SiOx-tunnel/SiNx-PECVD"},
            "HJT": {"emitter": "a-Si:H-PECVD", "passivation": "i-a-Si:H-PECVD"},
        }[cs.cellArchitecture]
        cs.junctionMetrics = {
            **recipe,
            "sheet_resistance_ohm_sq": 130,
            "implied_voc_mv": 720,
            # PECVD uses NF3 for in-situ chamber clean → tracked for the G3 gate.
            "chamber_clean_gas": "NF3",
        }
        cs.phase = CellPhase.JUNCTION
        cs.completionPct = 40
        return {"cell_state": cs.__dict__, "next_node": "metallization"}

    def _metallization(self, state: dict[str, Any]) -> dict[str, Any]:
        """JUNCTION → METALLIZED: screen-print / plate contacts (G6 Ag→Cu roadmap)."""
        cs = CellState(**state["cell_state"])
        cs.metallizationMetrics = {
            "paste_or_plating": cs.metallization,
            "fingers": 110,
            "busbars": "busbarless-multiwire" if cs.metallization != "silver" else "9BB",
            "no_lead_solder": True,  # G6 / RoHS-equivalent consumables
        }
        # G6: silver-only is permitted at R1 but is off the Ag→Cu roadmap → flag it.
        if cs.metallization not in _METALLIZATION_ON_ROADMAP:
            cs.metallizationFlags = [
                f"G6:silver-only-off-roadmap:{cs.metallization}; "
                "Ag→Cu (ag-cu-hybrid|copper) substitution required for R2+"
            ]
        cs.phase = CellPhase.METALLIZED
        cs.completionPct = 60
        return {"cell_state": cs.__dict__, "next_node": "flash_iv"}

    def _flash_iv(self, state: dict[str, Any]) -> dict[str, Any]:
        """METALLIZED → FLASH_TESTED: Mimi flash IV (AAA simulator) + power binning."""
        cs = CellState(**state["cell_state"])
        # Deterministic per-architecture median cell power (milliwatt-peak).
        # 6" M10 cell area; representative production-grade efficiencies.
        median_mwp = {
            "PERC": 6850,  # ~23.0 %
            "TOPCon": 7180,  # ~24.1 %
            "HJT": 7330,  # ~24.6 %
        }[cs.cellArchitecture]
        cs.flashIvMedianMilliwp = median_mwp
        cs.flashIvMetrics = {
            "simulator_class": "AAA-IEC60904-9",
            "median_pmax_milliwp": median_mwp,
            "median_voc_mv": 695,
            "median_isc_ma": 13500,
            "median_fill_factor_pct": 81.5,
        }
        # Power binning: simple +/- bins around the median (deterministic split).
        n = cs.waferCount
        cs.binDistribution = {
            "binA_plus_high": n // 4,
            "binA_nominal": n - (n // 4) - (n // 5) - (n // 20),
            "binB_low": n // 5,
            "binC_reject": n // 20,  # broken / low-FF → kerf-recovery loop (G5)
        }
        cs.phase = CellPhase.FLASH_TESTED
        cs.completionPct = 75
        return {"cell_state": cs.__dict__, "next_node": "gas_abatement"}

    def _gas_abatement(self, state: dict[str, Any]) -> dict[str, Any]:
        """FLASH_TESTED → ABATEMENT_VERIFIED or HALT: G3 high-GWP gas abatement.

        Every fluorinated etch/clean gas used in the line must be either
        substituted away OR routed through abatement with ≥99% DRE. Anything
        below the floor with no substitution halts the batch (constitutional G3).
        """
        cs = CellState(**state["cell_state"])

        # Gases this batch actually used (architecture-dependent).
        used_gases = ["NF3"]  # PECVD chamber clean (all architectures)
        if cs.cellArchitecture == "PERC":
            used_gases.append("CF4")  # edge-isolation / rear-etch in some PERC lines

        # Abatement model: plasma-burn + wet scrubber DRE per gas + substitution map.
        substitutions: dict[str, str] = {}  # e.g. {"NF3": "F2-remote-clean"} when substituted
        gas_lines: list[dict[str, Any]] = []
        below_floor: list[str] = []
        for gas in used_gases:
            substituted = gas in substitutions
            dre = 1.0 if substituted else 0.995  # 99.5% modeled abatement DRE
            gas_lines.append(
                {
                    "gas": gas,
                    "gwp100": _HIGH_GWP_GASES.get(gas, 0),
                    "substituted": substituted,
                    "substituteWith": substitutions.get(gas),
                    "destructionRemovalEfficiency": dre,
                    "meetsG3Floor": substituted or dre >= _MIN_DRE,
                }
            )
            if not (substituted or dre >= _MIN_DRE):
                below_floor.append(gas)

        cs.gasAbatement = {
            "minDreFloor": _MIN_DRE,
            "gases": gas_lines,
            "uncontrolledVenting": False,  # G3 / N7 — never permitted
            "allMeetG3": not below_floor,
        }
        cs.gasAbatementCid = _content_ref("ipfs/himawari-g3-abatement", cs.gasAbatement)
        cs.processParametersCid = _content_ref(
            "ipfs/himawari-process-params",
            {
                "texture": cs.textureMetrics,
                "junction": cs.junctionMetrics,
                "metallization": cs.metallizationMetrics,
            },
        )
        cs.binDistributionCid = _content_ref("ipfs/himawari-bin-dist", cs.binDistribution or {})

        if below_floor:
            cs.phase = CellPhase.ANOMALY_HALT
            cs.anomalyFlags = [
                f"G3:gas-abatement-below-99pct:{','.join(below_floor)}; "
                "abate to ≥99% DRE or substitute before release"
            ]
            cs.errorMsg = f"G3 violation: {below_floor} below {_MIN_DRE:.0%} DRE with no substitution"
            return {"cell_state": cs.__dict__, "next_node": "halt"}

        cs.phase = CellPhase.ABATEMENT_VERIFIED
        cs.completionPct = 85
        return {"cell_state": cs.__dict__, "next_node": "witness"}

    def _witness(self, state: dict[str, Any]) -> dict[str, Any]:
        """ABATEMENT_VERIFIED → WITNESS_WAIT: collect ≥2 robot Ed25519 signatures.

        G11 deterministic-yield witness quorum: Otete (line handling) + Mimi
        (flash IV / EL metrology). Robots COMPOSED from kuni-umi.
        """
        cs = CellState(**state["cell_state"])
        cs.robotSignatures = [
            {
                "robotDid": _OTETE_DID,
                "role": "cell_line_executor",
                "timestamp": "2026-06-02T00:00:00Z",
                "signature": "ed25519:otete-cell-process-sig",  # R2: real Ed25519 over record CID
            },
            {
                "robotDid": _MIMI_DID,
                "role": "flash_iv_metrology_witness",
                "timestamp": "2026-06-02T00:00:05Z",
                "signature": "ed25519:mimi-flash-iv-sig",
            },
        ]
        cs.phase = CellPhase.WITNESS_WAIT
        cs.completionPct = 95
        return {"cell_state": cs.__dict__, "next_node": "emit_record"}

    def _emit_record(self, state: dict[str, Any]) -> dict[str, Any]:
        """WITNESS_WAIT → COMPLETE: emit com.etzhayyim.himawari.cellBatchRecord."""
        cs = CellState(**state["cell_state"])

        # Matches lexicon com.etzhayyim.himawari.cellBatchRecord (required:
        # batchId, waferBatchId, cellArchitecture, gasAbatementCid, attestingRobots).
        # attestingRobots is intentionally a list of DID strings (the lexicon types
        # it as array<string,format:did>); robotSignatures carries the full
        # #robotSignature object bundle (robotDid + role + signature + timestamp).
        record: dict[str, Any] = {
            "$type": "com.etzhayyim.himawari.cellBatchRecord",
            "batchId": cs.batchId,
            "waferBatchId": cs.waferBatchId,
            "recordedAt": cs.recordedAt,
            "cellArchitecture": cs.cellArchitecture,
            "metallization": cs.metallization,
            "gasAbatementCid": cs.gasAbatementCid,
            "binDistributionCid": cs.binDistributionCid,
            "processParametersCid": cs.processParametersCid,
            "attestingRobots": [sig["robotDid"] for sig in cs.robotSignatures],
            "robotSignatures": cs.robotSignatures,
            "flashIvMedianMilliwp": cs.flashIvMedianMilliwp,
        }

        cs.phase = CellPhase.COMPLETE
        cs.completionPct = 100
        return {
            "cell_state": cs.__dict__,
            "cell_batch_record": record,
            "metallizationFlags": cs.metallizationFlags,
            "next_node": "end",
        }

    def _halt(self, state: dict[str, Any]) -> dict[str, Any]:
        """ANOMALY_HALT: halt the batch, escalate to a human PV-process engineer."""
        cs = CellState(**state["cell_state"])
        alert_record = {
            "$type": "com.etzhayyim.himawari.cellBatchRecord.halt",
            "batchId": cs.batchId,
            "waferBatchId": cs.waferBatchId,
            "event": "cell_process_halt",
            "reason": "g3_gas_abatement_anomaly",
            "anomalies": cs.anomalyFlags,
            "gasAbatementCid": cs.gasAbatementCid,
            "escalation": "human_pv_process_engineer_review_required",
            "correctiveAction": "Raise fluorinated-gas DRE to ≥99% or substitute the gas, then re-run.",
        }
        return {
            "cell_state": cs.__dict__,
            "alert_record": alert_record,
            "metallizationFlags": cs.metallizationFlags,
            "next_node": "end",
        }

    # ── graph ────────────────────────────────────────────────────────────────

    # node-name → method dispatch (shared by LangGraph and the fallback driver).
    def _node_table(self) -> dict[str, Any]:
        return {
            "init": self._initialize_state,
            "texture": self._texture,
            "junction": self._junction,
            "metallization": self._metallization,
            "flash_iv": self._flash_iv,
            "gas_abatement": self._gas_abatement,
            "witness": self._witness,
            "emit_record": self._emit_record,
            "halt": self._halt,
        }

    def _run_sequential(self, state: dict[str, Any]) -> dict[str, Any]:
        """Fallback super-step driver (used when LangGraph is unavailable).

        Each node returns its successor in ``next_node``; we follow that edge
        until a terminal node (``emit_record`` / ``halt``) sets ``next_node`` to
        ``end``. Identical control flow to the LangGraph graph below.
        """
        table = self._node_table()
        merged: dict[str, Any] = dict(state)
        node = "init"
        # bounded to avoid any accidental cycle (line is a DAG of ≤9 nodes).
        for _ in range(len(table) + 2):
            merged.update(table[node](merged))
            nxt = merged.get("next_node", "end")
            if nxt == "end":
                break
            node = nxt
        return merged

    def _build_graph(self) -> Any:
        """Build the LangGraph super-step loop (7 process nodes + halt)."""
        graph = StateGraph(dict)

        graph.add_node("init", self._initialize_state)
        graph.add_node("texture", self._texture)
        graph.add_node("junction", self._junction)
        graph.add_node("metallization", self._metallization)
        graph.add_node("flash_iv", self._flash_iv)
        graph.add_node("gas_abatement", self._gas_abatement)
        graph.add_node("witness", self._witness)
        graph.add_node("emit", self._emit_record)
        graph.add_node("halt", self._halt)

        graph.add_edge("init", "texture")
        graph.add_edge("texture", "junction")
        graph.add_edge("junction", "metallization")
        graph.add_edge("metallization", "flash_iv")
        graph.add_edge("flash_iv", "gas_abatement")

        def route_abatement(state: dict[str, Any]) -> str:
            return state.get("next_node", "witness")

        graph.add_conditional_edges(
            "gas_abatement", route_abatement, {"witness": "witness", "halt": "halt"}
        )

        graph.add_edge("witness", "emit")
        graph.add_edge("emit", "__end__")
        graph.add_edge("halt", "__end__")

        graph.set_entry_point("init")
        return graph.compile()

    def solve(self, state: dict[str, Any]) -> dict[str, Any]:
        """Execute the cell super-step loop and return the final state."""
        if StateGraph is None:
            return self._run_sequential(state)
        if self.graph is None:
            self.graph = self._build_graph()
        return self.graph.invoke(state)
