from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    material_id: str
    compliance_cleared: bool
    is_hazardous: bool

def validate_regulation(state: ProcurementState):
    # Simulated regulatory check for controlled substance
    state['compliance_cleared'] = True
    return 'compliance_verified'

def check_hazmat(state: ProcurementState):
    state['is_hazardous'] = True
    return 'hazmat_classified'

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_regulation)
graph.add_node('hazmat', check_hazmat)
graph.add_edge('validate', 'hazmat')
graph.add_edge('hazmat', END)
graph.set_entry_point('validate')
graph = graph.compile()