from langgraph.graph import StateGraph, END
from typing import TypedDict

class ProcurementState(TypedDict):
    purity: float
    compliance_docs: bool
    is_approved: bool

def validate_quality(state: ProcurementState):
    state['is_approved'] = state['purity'] >= 99.0 and state['compliance_docs']
    return state

def safety_check(state: ProcurementState):
    print(f"Executing safety protocols for API: {state['is_approved']}")
    return state

graph = StateGraph(ProcurementState)
graph.add_node("validate", validate_quality)
graph.add_node("safety", safety_check)
graph.set_entry_point("validate")
graph.add_edge("validate", "safety")
graph.add_edge("safety", END)
graph = graph.compile()