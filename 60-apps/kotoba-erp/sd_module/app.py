import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from kotoba_langgraph import _cbor as cbor2
from kotoba_langgraph import StateGraph, START, END

from src.use_cases.billing import (
    GenerateBillingState, parse_billing_request, fetch_sales_order, check_so_exists,
    generate_lines, validate_billing, check_validation, post_billing, reject_billing
)

builder = StateGraph(GenerateBillingState)
builder.add_node("parse", parse_billing_request)
builder.add_node("fetch_so", fetch_sales_order)
builder.add_node("generate_lines", generate_lines)
builder.add_node("validate", validate_billing)
builder.add_node("post", post_billing)
builder.add_node("reject", reject_billing)

builder.add_edge(START, "parse")
builder.add_edge("parse", "fetch_so")
builder.add_conditional_edges("fetch_so", check_so_exists, {
    "reject": "reject",
    "generate_lines": "generate_lines"
})
builder.add_edge("generate_lines", "validate")
builder.add_conditional_edges("validate", check_validation, {
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
            if result_state.get("vbrk"):
                output["billing_id"] = result_state["vbrk"].vbeln
                
            return bytes(cbor2.dumps(output))
except ImportError:
    pass
