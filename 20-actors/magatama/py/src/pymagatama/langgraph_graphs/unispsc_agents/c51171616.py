from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity: float
    has_coa: bool
    compliant: bool

def validate_purity(state: ProcurementState):
    state['compliant'] = state['purity'] >= 99.0
    return state

def check_documentation(state: ProcurementState):
    state['compliant'] = state['compliant'] and state['has_coa']
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_documentation', check_documentation)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_documentation')
graph.add_edge('check_documentation', END)
graph = graph.compile()
