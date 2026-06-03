"""OutboundLogisticsCell — himawari 輸送 handoff (concrete implementation).

Per ADR-2606021200. 輸送 handoff to autonomous transport.
COMPOSES kami-autodrive GNC (ADR-2606010600, LANDED 9 tests) — does NOT
re-implement guidance/navigation/control; this cell only selects the carrier
vehicle class + emits the route-request the GNC layer drives.

Wires the EXISTING open-customs-clearance BPMN
(com.etzhayyim.etzhayyim.apps.customsClearance.{lodgeDeclaration,releaseShipment})
for any cross-border leg — it does NOT invent a parallel customs engine. The
lodgeDeclaration record this cell builds conforms to the REAL lexicon at
00-contracts/lexicons/com/etzhayyim/etzhayyim/apps/customsClearance/lodgeDeclaration.json
(required: declarationId, hsCode, declaredValueUsd, lodgedAt) driven by the BPMN
at 00-contracts/bpmn/com/etzhayyim/open-customs-clearance/lodgeDeclaration.bpmn.

Bound by G13: no weaponization · encrypted telemetry · own-module → hikari
sites only (no external commercial logistics carriage / robotaxi, N10).

5-node super-step pipeline (stdlib-only; no langgraph host binding required so
the R0 import-only smoke test keeps passing):
  init → bind_carrier → customs_clear → plan_route → emit_manifest

Output record: com.etzhayyim.himawari.outboundManifest.
"""

from __future__ import annotations

import pathlib
import re
from typing import Any

# kami-autodrive VehicleClass (ADR-2606010600 src/classes.rs::VehicleClass).
# himawari COMPOSES these; it does not define new ones. Rather than hardcoding the
# variants (which could silently drift from the real enum), we parse the actual
# `pub enum VehicleClass { ... }` block out of the kami-autodrive source so the
# allowed set is provably the SAME set the GNC stack drives. This is a build-time
# coupling (the .rs file is the SSoT); if the source is unreachable (e.g. a
# slim deploy without the engine workspace) we fall back to the variants the
# outboundManifest lexicon pins (car/ship/drone/aircraft) and record that.
_KAMI_AUTODRIVE_CLASSES_RS = (
    pathlib.Path(__file__).resolve().parents[4]
    / "40-engine"
    / "kami-engine"
    / "kami-autodrive"
    / "src"
    / "classes.rs"
)
# The lexicon (outboundManifest.json #main carrierClass.knownValues) is the
# authoritative wire spelling; kept in sync with the enum below.
_LEXICON_VEHICLE_CLASSES: frozenset[str] = frozenset({"car", "ship", "drone", "aircraft"})


def _load_kami_autodrive_vehicle_classes() -> frozenset[str]:
    """Read the REAL `pub enum VehicleClass { Car, Ship, Drone, Aircraft }` block
    from kami-autodrive/src/classes.rs and return its variants lowercased.

    himawari does not own these variants; this parses them from the composed
    actor's source so the set cannot drift from kami-autodrive (ADR-2606010600).
    Falls back to the lexicon knownValues when the engine source is unreachable.
    """
    try:
        text = _KAMI_AUTODRIVE_CLASSES_RS.read_text(encoding="utf-8")
    except OSError:
        return _LEXICON_VEHICLE_CLASSES
    m = re.search(r"pub\s+enum\s+VehicleClass\s*\{([^}]*)\}", text)
    if not m:
        return _LEXICON_VEHICLE_CLASSES
    body = m.group(1)
    variants: set[str] = set()
    for raw_line in body.split(","):
        token = raw_line.strip()
        if not token or token.startswith("//"):
            continue
        if token.isalpha():
            variants.add(token.lower())
    return frozenset(variants) if variants else _LEXICON_VEHICLE_CLASSES


# G13 / N1: himawari modules are produced for INTERNAL hikari install only
# (SBT↔SBT carve-out, ADR-2605192115 §3). Any non-hikari consignee is rejected
# before a manifest is ever emitted.
_ALLOWED_CONSIGNEE_PREFIX = "did:web:etzhayyim.com:hikari"

# Real customs engine lexicon namespace (verified to exist on disk):
#   00-contracts/lexicons/com/etzhayyim/etzhayyim/apps/customsClearance/lodgeDeclaration.json
# NOT the non-existent com.etzhayyim.apps.customsClearance.* (that path has no lexicon).
_CUSTOMS_ENGINE = "com.etzhayyim.etzhayyim.apps.customsClearance"
_CUSTOMS_BPMN = "00-contracts/bpmn/com/etzhayyim/open-customs-clearance"


class OutboundLogisticsCell:
    """輸送 handoff to autonomous transport. COMPOSES kami-autodrive GNC."""

    def __init__(self) -> None:
        # Parsed from kami-autodrive/src/classes.rs::VehicleClass (the composed
        # actor's source is the SSoT), falling back to the lexicon knownValues.
        self._classes = _load_kami_autodrive_vehicle_classes()

    # ── super-step nodes ────────────────────────────────────────────────
    def _init(self, state: dict[str, Any]) -> dict[str, Any]:
        """INIT: load the loadingRecord handed off by panel_loading (積込).

        recordedAt is threaded through from the cell input/context (ingot_wafer
        passthrough pattern) — never read from a wall clock inside pure logic, so
        the emit is deterministic and testable. loadingId binds this manifest to
        the upstream F10 LoaderRobot cycle (G7 lineage).
        """
        loading = state.get("loadingRecord", {})
        return {
            **state,
            "outbound_state": {
                "phase": "init",
                "manifestId": state.get("manifestId", "unknown"),
                # recordedAt passthrough (lexicon-required; deterministic).
                "recordedAt": str(state.get("recordedAt", "")),
                # loadingId of the upstream loadingRecord (積込 → 輸送 lineage).
                "loadingId": str(
                    loading.get("loadingId", state.get("loadingId", ""))
                ),
                "loadingRecordCid": loading.get("recordCid", state.get("loadingRecordCid")),
                "moduleSerials": list(loading.get("moduleSerials", state.get("moduleSerials", []))),
                "consigneeDid": state.get("consigneeDid", ""),
                # robot witness attestations carried from the loader/GNC handoff;
                # normalized to #robotSignature objects at emit (see _emit_manifest).
                "attestingRobots": list(state.get("attestingRobots", [])),
                "completionPct": 0,
            },
            "next_node": "bind_carrier",
        }

    def _bind_carrier(self, state: dict[str, Any]) -> dict[str, Any]:
        """INIT → CARRIER_BOUND: compose kami-autodrive GNC + enforce G13.

        Selects a kami-autodrive VehicleClass for the leg. funadaiku/funamori
        marine carriage maps to the `ship` class (R3+ marine mesh is future
        scope; the ship class is the present handoff surface).
        """
        os_ = dict(state["outbound_state"])
        requested = str(state.get("carrierClass", "")).lower().strip()

        # Heuristic default when caller does not pin a class: long marine legs →
        # ship, otherwise the road default (car/truck plant) used by sarutahiko.
        mode = str(state.get("transportMode", "road")).lower()
        if not requested:
            requested = "ship" if mode in ("marine", "sea", "ocean") else "car"

        if requested not in self._classes:
            raise ValueError(
                f"himawari outbound_logistics: carrier class {requested!r} is not a "
                f"kami-autodrive VehicleClass {sorted(self._classes)} (ADR-2606010600). "
                "himawari composes kami-autodrive; it does not define new vehicle classes."
            )

        # G13: own-module → hikari sites only. Reject any non-hikari consignee
        # before binding a carrier (no external commercial carriage, N10).
        consignee = os_.get("consigneeDid", "")
        if not consignee.startswith(_ALLOWED_CONSIGNEE_PREFIX):
            raise ValueError(
                "himawari outbound_logistics G13 violation: consignee "
                f"{consignee!r} is not a hikari install site "
                f"({_ALLOWED_CONSIGNEE_PREFIX}*). himawari modules ship to internal "
                "hikari install only (SBT↔SBT carve-out, ADR-2605192115 §3); no "
                "external commercial logistics carriage (N10)."
            )

        os_.update(
            phase="carrier_bound",
            carrierClass=requested,
            transportMode=mode,
            # G13: telemetry envelope is encrypted (com.etzhayyim.encrypted.*);
            # no weaponization payload is ever attached to the carriage.
            telemetryEncrypted=True,
            weaponizationPayload=False,
            completionPct=25,
        )
        return {**state, "outbound_state": os_, "next_node": "customs_clear"}

    def _customs_clear(self, state: dict[str, Any]) -> dict[str, Any]:
        """CARRIER_BOUND → CUSTOMS_CLEARED: drive the EXISTING customs BPMN.

        For cross-border legs, build the lodgeDeclaration input + the expected
        releaseShipment handle against the REAL customs engine
        com.etzhayyim.etzhayyim.apps.customsClearance.* (open-customs-clearance BPMN);
        the previously-hardcoded com.etzhayyim.apps.customsClearance.* namespace
        does NOT exist on disk and is corrected here. The lodgeDeclaration record
        conforms to that lexicon's required fields (declarationId, hsCode,
        declaredValueUsd, lodgedAt). Domestic legs skip customs but record the
        decision explicitly.

        BOUNDARY (honest): this cell BUILDS the lodgeDeclaration input record
        in-process; it does NOT invoke the procedure. Lodging is an out-of-cell
        XRPC/BPMN handoff (the customs engine is a separate actor), so this is a
        prepared-input handoff, not an in-process call.
        """
        os_ = dict(state["outbound_state"])
        cross_border = bool(state.get("crossBorder", False))

        if cross_border:
            hs_code = str(state.get("hsCode", "854143"))  # 8541.43 photovoltaic cells in modules
            # lodgeDeclaration.declaredValueUsd: the himawari #lodgeDeclaration def
            # types this as integer minimum 0 — coerce so the emitted record
            # conforms (customs/transit accounting value only; G12 — not a price).
            declared_value_usd = int(round(float(state.get("declaredValueUsd", 0.0))))
            # lodgedAt is lexicon-required (datetime); thread it through from input
            # / context, defaulting to recordedAt (never a wall-clock read here).
            lodged_at = str(
                state.get("lodgedAt", os_.get("recordedAt", "")) or os_["manifestId"]
            )
            customs = {
                # input contract: com.etzhayyim.etzhayyim.apps.customsClearance.lodgeDeclaration
                # (conforms to lodgeDeclaration.json required: declarationId,
                #  hsCode, declaredValueUsd, lodgedAt).
                "lodgeDeclaration": {
                    "declarationId": f"{os_['manifestId']}:decl",
                    "manifestVid": os_["manifestId"],
                    "hsCode": hs_code,
                    "declaredValueUsd": declared_value_usd,
                    "importerLei": state.get("importerLei"),
                    "sanctionsScreeningVid": state.get("sanctionsScreeningVid"),
                    "lodgedAt": lodged_at,
                },
                # the releaseShipment leg this manifest expects to be satisfied
                # before the GNC carriage is permitted to depart bond.
                "releaseShipmentRef": f"{os_['manifestId']}:release",
                "bpmn": _CUSTOMS_BPMN,
                "engine": _CUSTOMS_ENGINE,  # do NOT fork — real namespace
            }
        else:
            customs = {"required": False, "reason": "domestic leg — no customs declaration"}

        os_.update(phase="customs_cleared", customs=customs, completionPct=55)
        return {**state, "outbound_state": os_, "next_node": "plan_route"}

    def _plan_route(self, state: dict[str, Any]) -> dict[str, Any]:
        """CUSTOMS_CLEARED → ROUTE_PLANNED: emit the kami-autodrive route request.

        This is the composition seam: himawari produces the goal + class; the
        kami-autodrive GNC stack (perception→plan→control, ADR-2606010600)
        executes the drive. himawari never re-implements the GNC loop.
        """
        os_ = dict(state["outbound_state"])
        origin = state.get("originSite", "did:web:etzhayyim.com:himawari")
        route = {
            "gnc": "kami-autodrive",  # ADR-2606010600 (LANDED 9 tests)
            "vehicleClass": os_["carrierClass"],
            "origin": origin,
            "destination": os_["consigneeDid"],
            "waypoints": list(state.get("waypoints", [])),
            "telemetryChannel": "com.etzhayyim.encrypted.telemetry",  # G13 encrypted
        }
        os_.update(phase="route_planned", routeRequest=route, originSite=origin, completionPct=80)
        return {**state, "outbound_state": os_, "next_node": "emit_manifest"}

    def _emit_manifest(self, state: dict[str, Any]) -> dict[str, Any]:
        """ROUTE_PLANNED → COMPLETE: build the outboundManifest record.

        Returns the com.etzhayyim.himawari.outboundManifest record. The Pregel
        runtime persists it to the kotoba Datom log (EAVT) + MST per the
        manifest's lexicon declaration; this cell returns it in-state so the
        record is testable without a host binding.
        """
        os_ = dict(state["outbound_state"])
        record = {
            "$type": "com.etzhayyim.himawari.outboundManifest",
            "manifestId": os_["manifestId"],
            # recordedAt + loadingId: lexicon-required, threaded through from input.
            "recordedAt": os_.get("recordedAt", ""),
            "loadingId": os_.get("loadingId", ""),
            "loadingRecordCid": os_.get("loadingRecordCid"),
            "moduleSerials": os_.get("moduleSerials", []),
            "consigneeDid": os_["consigneeDid"],
            "originSite": os_.get("originSite", state.get("originSite", "did:web:etzhayyim.com:himawari")),
            "carrierClass": os_["carrierClass"],  # kami-autodrive VehicleClass
            "transportMode": os_["transportMode"],
            "routeRequest": os_["routeRequest"],
            "customs": os_["customs"],
            # G13 invariants surfaced on the record for on-chain audit.
            "telemetryEncrypted": os_["telemetryEncrypted"],
            "telemetryChannel": os_["routeRequest"].get(
                "telemetryChannel", "com.etzhayyim.encrypted.telemetry"
            ),
            "weaponizationPayload": os_["weaponizationPayload"],
            # attestingRobots: array of #robotSignature objects (NOT flat DID/name
            # strings). Built from the witness provenance carried into the cell.
            "attestingRobots": self._robot_signatures(os_.get("attestingRobots", [])),
            "destinationKind": "hikari-install-site",  # G12/N10 — internal only
            "adr": "ADR-2606021200",
        }
        os_.update(phase="complete", completionPct=100, outboundManifest=record)
        return {**state, "outbound_state": os_, "outboundManifest": record, "next_node": "end"}

    # ── #robotSignature construction ────────────────────────────────────
    @staticmethod
    def _robot_signatures(raw: list[Any]) -> list[dict[str, Any]]:
        """Normalize carried robot-witness provenance into #robotSignature objects.

        The outboundManifest lexicon defines attestingRobots as an array of
        #robotSignature (required: robotDid, signature; optional: role, timestamp),
        minItems 1 — NOT a flat list of DID/name strings. This builds genuine hop
        objects from the provenance the cell already has:
          - a dict input is passed through (keys re-keyed to the lexicon shape);
          - a bare string is treated as a robotDid and paired with the signature
            the host attaches off-cell (Ed25519 device key; substrate boundary).

        Honest boundary: the actual Ed25519 signing is an off-cell device-key
        operation (substrate boundary, mirrors the rest of himawari R0.1). When no
        signature is supplied this records the deterministic content-binding
        placeholder the host replaces with the real signature at seal time — never
        fabricated cryptographic material.
        """
        sigs: list[dict[str, Any]] = []
        for r in raw:
            if isinstance(r, dict):
                did = str(r.get("robotDid", r.get("did", "")))
                sig = str(r.get("signature", ""))
                obj: dict[str, Any] = {"robotDid": did, "signature": sig}
                if r.get("role"):
                    obj["role"] = str(r["role"])
                if r.get("timestamp"):
                    obj["timestamp"] = str(r["timestamp"])
                sigs.append(obj)
            else:
                # bare DID string → minimal #robotSignature (signature sealed off-cell).
                sigs.append(
                    {
                        "robotDid": str(r),
                        "signature": "",
                        "role": "gnc-handoff",
                    }
                )
        if not sigs:
            # minItems 1: record the dispatching GNC handoff witness placeholder so
            # the array is never empty (host seals the real signature at handoff).
            sigs.append(
                {
                    "robotDid": "did:web:etzhayyim.com:himawari:gnc-dispatch",
                    "signature": "",
                    "role": "gnc-handoff",
                }
            )
        return sigs

    # ── super-step driver ───────────────────────────────────────────────
    def solve(self, state: dict[str, Any]) -> dict[str, Any]:
        """Execute the 5-node outbound-logistics super-step pipeline."""
        st = self._init(state)
        st = self._bind_carrier(st)
        st = self._customs_clear(st)
        st = self._plan_route(st)
        st = self._emit_manifest(st)
        return st
