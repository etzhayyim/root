from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity_level: float
    safety_checked: bool
    approved: bool

def validate_purity(state: ProcurementState):
    state['approved'] = state['purity_level'] >= 99.0
    return 'validate_purity'

def check_compliance(state: ProcurementState):
    state['safety_checked'] = True
    return 'check_compliance'

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_purity)
graph.add_node('certify', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'certify')
graph.add_edge('certify', END)
app = graph.compile()
