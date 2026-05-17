from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_name: str
    spec_verified: bool
    adhesive_type: str

def validate_adhesive_specs(state: ProcurementState):
    # Business logic for adhesive dot procurement
    if state.get("adhesive_type") in ["permanent", "removable"]:
        return {"spec_verified": True}
    return {"spec_verified": False}

def finalize_order(state: ProcurementState):
    print(f"Processing order for {state['item_name']}")
    return {"spec_verified": True}

graph = StateGraph(ProcurementState)
graph.add_node("validate", validate_adhesive_specs)
graph.add_node("finalize", finalize_order)
graph.add_edge("validate", "finalize")
graph.add_edge("finalize", END)
graph.set_entry_point("validate")
app = graph.compile()