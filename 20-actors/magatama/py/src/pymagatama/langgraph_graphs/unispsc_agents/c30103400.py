from typing import TypedDict
from langgraph.graph import StateGraph, END

class IngotState(TypedDict):
    purity_level: float
    alloy_certified: bool
    inspection_passed: bool

def validate_purity(state: IngotState):
    state['inspection_passed'] = state['purity_level'] >= 99.9
    return state

def check_compliance(state: IngotState):
    return 'approved' if state['inspection_passed'] and state['alloy_certified'] else 'rejected'

graph = StateGraph(IngotState)
graph.add_node('validate', validate_purity)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.set_entry_point('validate')
graph.add_edge('compliance', END)
graph = graph.compile()
