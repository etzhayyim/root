from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity_level: float
    has_assay: bool
    is_verified: bool

def validate_purity(state: ProcurementState):
    state['is_verified'] = state['purity_level'] >= 0.999
    return state

def check_compliance(state: ProcurementState):
    return 'compliant' if state['is_verified'] and state['has_assay'] else 'flagged'

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_purity)
graph.add_node('check', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'check')
graph.add_edge('check', END)
graph = graph.compile()