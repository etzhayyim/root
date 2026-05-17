from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity_level: float
    compliant: bool

def validate_purity(state: ProcurementState):
    state['compliant'] = state['purity_level'] >= 99.0
    return state

def check_certification(state: ProcurementState):
    return {'compliant': state['compliant']}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_purity)
graph.add_node('certify', check_certification)
graph.add_edge('validate', 'certify')
graph.add_edge('certify', END)
graph.set_entry_point('validate')
graph = graph.compile()