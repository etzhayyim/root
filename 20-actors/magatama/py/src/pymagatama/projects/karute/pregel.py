"""karute Pregel — 31-pipeline LangGraph StateGraph mirroring actor-manifest.jsonld.

Phase 1 stub: every node returns ``{"status": "stub", "pipeline": "<name>"}``
so the graph compiles + serves via ``langgraph dev`` without requiring the
SDK / PDS / IPFS / L2 substrate to be live.

The node-name → pipeline-trigger mapping mirrors the XRPC NSIDs:

    create_patient                   app.etzhayyim.apps.karute.createPatient
    create_encounter                 app.etzhayyim.apps.karute.createEncounter
    create_soap_note                 app.etzhayyim.apps.karute.createSoapNote
    create_observation               app.etzhayyim.apps.karute.createObservation
    create_condition                 app.etzhayyim.apps.karute.createCondition
    create_medication_request        app.etzhayyim.apps.karute.createMedicationRequest
    create_service_request           app.etzhayyim.apps.karute.createServiceRequest
    create_dispense                  app.etzhayyim.apps.karute.createDispense
    create_homecare_episode          app.etzhayyim.apps.karute.createHomecareEpisode
    create_home_visit                app.etzhayyim.apps.karute.createHomeVisit
    grant_consent                    app.etzhayyim.apps.karute.grantConsent
    revoke_consent                   app.etzhayyim.apps.karute.revokeConsent
    list_consent                     app.etzhayyim.apps.karute.listConsent
    request_iryo_billing             app.etzhayyim.apps.karute.requestIryoBilling
    rekey_record                     app.etzhayyim.apps.karute.rekeyRecord
    redact_record                    app.etzhayyim.apps.karute.redactRecord
    list_tombstones                  app.etzhayyim.apps.karute.listTombstones
    list_audit_events                app.etzhayyim.apps.karute.listAuditEvents
    get_chart_summary                app.etzhayyim.apps.karute.getChartSummary
    export_fhir_bundle               app.etzhayyim.apps.karute.exportFhirBundle
    list_patients                    app.etzhayyim.apps.karute.listPatients
    get_patient                      app.etzhayyim.apps.karute.getPatient
    list_encounters                  app.etzhayyim.apps.karute.listEncounters
    list_soap_notes                  app.etzhayyim.apps.karute.listSoapNotes
    list_observations                app.etzhayyim.apps.karute.listObservations
    list_medications                 app.etzhayyim.apps.karute.listMedications
    list_orders                      app.etzhayyim.apps.karute.listOrders
    list_dispenses                   app.etzhayyim.apps.karute.listDispenses
    list_homecare_episodes           app.etzhayyim.apps.karute.listHomecareEpisodes
    list_home_visits                 app.etzhayyim.apps.karute.listHomeVisits
    health_karute                    app.etzhayyim.apps.karute.healthKarute
"""

from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph


class KaruteState(TypedDict, total=False):
    """The Pregel state passed between nodes.

    PHI is NEVER stored here — the encrypted envelope lives at the sidecar
    boundary (`@etzhayyim/sdk.encryptedWrite` returns a CID; only the CID
    crosses this graph).
    """

    pipeline: str
    input: dict[str, Any]
    encrypt_result: dict[str, Any]
    graph_result: dict[str, Any]
    audit_event: dict[str, Any]
    output: dict[str, Any]
    errors: list[str]


PIPELINES = [
    "create_patient",
    "create_encounter",
    "create_soap_note",
    "create_observation",
    "create_condition",
    "create_medication_request",
    "create_service_request",
    "create_dispense",
    "create_homecare_episode",
    "create_home_visit",
    "grant_consent",
    "revoke_consent",
    "list_consent",
    "request_iryo_billing",
    "rekey_record",
    "redact_record",
    "list_tombstones",
    "list_audit_events",
    "get_chart_summary",
    "export_fhir_bundle",
    "list_patients",
    "get_patient",
    "list_encounters",
    "list_soap_notes",
    "list_observations",
    "list_medications",
    "list_orders",
    "list_dispenses",
    "list_homecare_episodes",
    "list_home_visits",
    "health_karute",
]


def _stub_node(name: str):
    def node(state: KaruteState) -> KaruteState:
        return {
            **state,
            "pipeline": name,
            "output": {"status": "stub", "pipeline": name, "note": "Phase 1 — substrate seams pending"},
        }

    node.__name__ = name
    return node


def _route(state: KaruteState) -> str:
    """Dispatch to the requested pipeline.

    The langserver HTTP entrypoint passes ``state.pipeline`` to select the
    branch; unknown pipelines fall through to ``health_karute`` so the graph
    always converges.
    """
    requested = (state.get("pipeline") or "").strip()
    return requested if requested in PIPELINES else "health_karute"


def build_graph() -> StateGraph:
    builder: StateGraph = StateGraph(KaruteState)
    for name in PIPELINES:
        builder.add_node(name, _stub_node(name))
    builder.add_conditional_edges(START, _route, {name: name for name in PIPELINES})
    for name in PIPELINES:
        builder.add_edge(name, END)
    return builder


app = build_graph().compile()
