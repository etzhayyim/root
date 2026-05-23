from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity: float
    has_coa: bool
    compliant: bool

def validate_purity(state: ProcurementState):
    state['compliant'] = state['purity'] >= 99.0
    return state

def check_compliance(state: ProcurementState):
    return 'valid' if state['has_coa'] and state['compliant'] else 'reject'

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_purity)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
