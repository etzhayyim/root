import json
import wit_world
from typing import Dict, Any

import sys
import os
# Hack to allow importing from src if needed, though typically componentize-py handles -p src
sys.path.insert(0, os.path.dirname(__file__))

from src.use_cases.post_journal import (
    PostJournalState, parse_entry, validate_entry, check_validation, post_entry, reject_entry
)
from kotoba_langgraph import StateGraph, START, END, handle_invoke

# Build the LangGraph for the Financial Use Case
builder = StateGraph(PostJournalState)
builder.add_node("parse", parse_entry)
builder.add_node("validate", validate_entry)
builder.add_node("post", post_entry)
builder.add_node("reject", reject_entry)

builder.add_edge(START, "parse")
builder.add_edge("parse", "validate")
builder.add_conditional_edges("validate", check_validation, {
    "reject": "reject",
    "post": "post"
})
builder.add_edge("post", END)
builder.add_edge("reject", END)

# In production we would use KotobaCheckpointer here, but keeping it simple for the PoC
compiled = builder.compile()

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        """
        Entrypoint called by the kotoba-runtime.
        We use handle_invoke from kotoba_langgraph to decode CBOR, invoke the graph, and return CBOR.
        """
        return handle_invoke(ctx_cbor, compiled)
