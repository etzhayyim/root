from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PharmState(TypedDict):
    material_name: str
    purity: float
    compliance_docs: List[str]
    validation_status: bool

def validate_purity(state: PharmState):
    state['validation_status'] = state['purity'] >= 99.0
    return state

def check_compliance(state: PharmState):
    state['validation_status'] = state['validation_status'] and len(state['compliance_docs']) > 0
    return state

graph = StateGraph(PharmState)
graph.add_node("validate_purity", validate_purity)
graph.add_node("check_compliance", check_compliance)
graph.add_edge("validate_purity", "check_compliance")
graph.set_entry_point("validate_purity")
graph.add_edge("check_compliance", END)
graph = graph.compile()