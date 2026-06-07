import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from kotoba_langgraph import _cbor as cbor2
from kotoba_langgraph import StateGraph, START, END

from src.use_cases.close_opportunity import (
    CloseOpportunityState, parse_request, fetch_opportunity, check_opp_exists,
    update_stage, validate_opp, check_validation, save_opp, reject_opp
)

builder = StateGraph(CloseOpportunityState)
builder.add_node("parse", parse_request)
builder.add_node("fetch_opp", fetch_opportunity)
builder.add_node("update_stage", update_stage)
builder.add_node("validate", validate_opp)
builder.add_node("save", save_opp)
builder.add_node("reject", reject_opp)

builder.add_edge(START, "parse")
builder.add_edge("parse", "fetch_opp")
builder.add_conditional_edges("fetch_opp", check_opp_exists, {
    "reject": "reject",
    "update_stage": "update_stage"
})
builder.add_edge("update_stage", "validate")
builder.add_conditional_edges("validate", check_validation, {
    "reject": "reject",
    "save": "save"
})
builder.add_edge("save", END)
builder.add_edge("reject", END)

compiled = builder.compile()

try:
    import wit_world
    class WitWorld(wit_world.WitWorld):
        def run(self, ctx_cbor: bytes) -> bytes:
            try:
                payload = cbor2.loads(ctx_cbor)
                if not isinstance(payload, dict):
                    payload = {}
            except Exception:
                payload = {}
                
            initial_state = {
                "input_data": payload,
                "errors": []
            }
            
            result_state = compiled.invoke(initial_state)
            
            output = {
                "status": result_state.get("status", "UNKNOWN"),
                "errors": result_state.get("errors", [])
            }
            if result_state.get("opportunity"):
                output["opportunity_id"] = result_state["opportunity"].Id
                output["stage"] = result_state["opportunity"].StageName
                
            return bytes(cbor2.dumps(output))
except ImportError:
    pass
