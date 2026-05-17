from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class PharmaProcurementState(TypedDict):
    batch_id: str
    purity_level: float
    coa_verified: bool
    compliant: bool

def validate_coa(state: PharmaProcurementState):
    state['coa_verified'] = state['purity_level'] >= 99.0
    return state

def check_compliance(state: PharmaProcurementState):
    state['compliant'] = state['coa_verified']
    return state

graph = StateGraph(PharmaProcurementState)
graph.add_node('validate_coa', validate_coa)
graph.add_node('check_compliance', check_compliance)
graph.set_entry_point('validate_coa')
graph.add_edge('validate_coa', 'check_compliance')
graph.add_edge('check_compliance', END)
app = graph.compile()