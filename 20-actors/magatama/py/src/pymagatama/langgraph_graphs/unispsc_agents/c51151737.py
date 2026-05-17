from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity_level: float
    gmp_verified: bool
    safety_clearance: bool

def validate_purity(state: ProcurementState):
    return {'safety_clearance': state['purity_level'] >= 99.0}

def check_compliance(state: ProcurementState):
    return {'safety_clearance': state['gmp_verified'] and state['safety_clearance']}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_purity)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
app = graph.compile()