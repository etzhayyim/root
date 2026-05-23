from typing import TypedDict
from langgraph.graph import StateGraph, END

class FlucytosineState(TypedDict):
    batch_id: str
    purity_level: float
    compliance_cleared: bool

def validate_purity(state: FlucytosineState):
    if state['purity_level'] >= 99.0:
        return {'compliance_cleared': True}
    return {'compliance_cleared': False}

def update_procurement_status(state: FlucytosineState):
    print(f"Processing batch {state['batch_id']}: Status {'Clear' if state['compliance_cleared'] else 'Reject'}")
    return state

graph = StateGraph(FlucytosineState)
graph.add_node("validate", validate_purity)
graph.add_node("status", update_procurement_status)
graph.add_edge("validate", "status")
graph.add_edge("status", END)
graph.set_entry_point("validate")
compiled_graph = graph.compile()
