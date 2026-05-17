from typing import TypedDict
from langgraph.graph import StateGraph, END

class MetaxaloneState(TypedDict):
    batch_id: str
    quality_status: str
    compliance_checked: bool

def validate_gmp(state: MetaxaloneState):
    print(f"Validating GMP status for batch: {state['batch_id']}")
    return {"compliance_checked": True}

def update_status(state: MetaxaloneState):
    return {"quality_status": "Verified" if state['compliance_checked'] else "Rejected"}

graph = StateGraph(MetaxaloneState)
graph.add_node("validate", validate_gmp)
graph.add_node("update", update_status)
graph.add_edge("validate", "update")
graph.add_edge("update", END)
graph.set_entry_point("validate")
compiled_graph = graph.compile()