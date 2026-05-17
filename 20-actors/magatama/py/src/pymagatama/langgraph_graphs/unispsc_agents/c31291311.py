from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    part_id: str
    purity_level: float
    inspection_passed: bool
    security_clearance_required: bool

def validate_purity(state: ProcurementState):
    # Perform high-precision material validation
    state['inspection_passed'] = state['purity_level'] >= 99.9
    return state

def check_customs_risk(state: ProcurementState):
    # Dual-use assessment logic
    state['security_clearance_required'] = True
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_purity)
graph.add_node('risk_check', check_customs_risk)
graph.set_entry_point('validate')
graph.add_edge('validate', 'risk_check')
graph.add_edge('risk_check', END)
graph = graph.compile()