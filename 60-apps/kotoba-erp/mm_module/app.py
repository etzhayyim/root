import wit_world
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from src.use_cases.receive_goods import (
    ReceiveGoodsState, parse_receipt, fetch_po, check_po_exists, 
    validate_receipt, check_validation, post_receipt, reject_receipt
)
from kotoba_langgraph import StateGraph, START, END, handle_invoke

builder = StateGraph(ReceiveGoodsState)
builder.add_node("parse", parse_receipt)
builder.add_node("fetch_po", fetch_po)
builder.add_node("validate", validate_receipt)
builder.add_node("post", post_receipt)
builder.add_node("reject", reject_receipt)

builder.add_edge(START, "parse")
builder.add_edge("parse", "fetch_po")
builder.add_conditional_edges("fetch_po", check_po_exists, {
    "reject": "reject",
    "validate": "validate"
})
builder.add_conditional_edges("validate", check_validation, {
    "reject": "reject",
    "post": "post"
})
builder.add_edge("post", END)
builder.add_edge("reject", END)

compiled = builder.compile()

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
