import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from typing import TypedDict, List
from kotoba_langgraph import _cbor as cbor2
from kotoba_langgraph import StateGraph, START, END

from src.use_cases.post_journal import (
    PostJournalState, parse_entry, validate_entry, check_validation, post_entry, reject_entry
)
from src.use_cases.process_event import (
    EventRouterState, parse_incoming_payload, map_mm_receipt, route_event
)

# We can combine the states for the master graph
class AppState(TypedDict):
    ctx_payload: dict
    mapped_journal_data: dict | None
    route: str

    # Fields from PostJournalState
    entry_data: dict
    bkpf: object | None
    validation_errors: List[str]
    status: str

def init_post_journal(state: AppState) -> dict:
    """Pass mapped data to the entry_data for PostJournal flow."""
    return {"entry_data": state["mapped_journal_data"]}

builder = StateGraph(AppState)

# Router nodes
builder.add_node("parse_incoming_payload", parse_incoming_payload)
builder.add_node("map_mm_receipt", map_mm_receipt)
builder.add_node("init_post_journal", init_post_journal)

# Post Journal nodes
builder.add_node("parse_entry", parse_entry)
builder.add_node("validate_entry", validate_entry)
builder.add_node("post", post_entry)
builder.add_node("reject", reject_entry)

# Edges
builder.add_edge(START, "parse_incoming_payload")
builder.add_conditional_edges("parse_incoming_payload", route_event, {
    "map_mm_receipt": "map_mm_receipt",
    "direct_journal": "init_post_journal"
})

builder.add_edge("map_mm_receipt", "init_post_journal")
builder.add_edge("init_post_journal", "parse_entry")
builder.add_edge("parse_entry", "validate_entry")

builder.add_conditional_edges("validate_entry", check_validation, {
    "reject": "reject",
    "post": "post"
})

builder.add_edge("post", END)
builder.add_edge("reject", END)

compiled = builder.compile()

try:
    import wit_world
    class WitWorld(wit_world.WitWorld):
        def run(self, ctx_cbor: bytes) -> bytes:
            """
            Entrypoint called by the kotoba-runtime.
            We handle the CBOR decoding manually here since we want to pass it as ctx_payload.
            """
            try:
                payload = cbor2.loads(ctx_cbor)
                if not isinstance(payload, dict):
                    payload = {}
            except Exception:
                payload = {}

            initial_state = {
                "ctx_payload": payload,
                "validation_errors": []
            }

            # Invoke the compiled graph
            result_state = compiled.invoke(initial_state)

            # We only want to return specific parts of the state to the caller
            output = {
                "status": result_state.get("status", "UNKNOWN"),
                "errors": result_state.get("validation_errors", [])
            }
            if result_state.get("bkpf"):
                output["entry_id"] = result_state["bkpf"].belnr

            return bytes(cbor2.dumps(output))
except ImportError:
    pass
