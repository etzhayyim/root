from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class StructuralState(TypedDict):
    load_capacity: float
    bolt_material: str
    compliance_docs: List[str]
    validation_status: bool

def validate_load_capacity(state: StructuralState):
    state['validation_status'] = state['load_capacity'] > 0
    return state

def check_certification(state: StructuralState):
    state['validation_status'] = state['validation_status'] and len(state['compliance_docs']) > 0
    return state

graph = StateGraph(StructuralState)
graph.add_node("validate_load", validate_load_capacity)
graph.add_node("check_cert", check_certification)
graph.add_edge("validate_load", "check_cert")
graph.add_edge("check_cert", END)
graph.set_entry_point("validate_load")
graph = graph.compile()