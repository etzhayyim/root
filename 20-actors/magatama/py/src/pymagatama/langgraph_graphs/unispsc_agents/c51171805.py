from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity: float
    gmp_status: bool
    is_compliant: bool

def validate_api_purity(state: ProcurementState):
    state['is_compliant'] = state['purity'] >= 99.0 and state['gmp_status']
    return state

def check_compliance(state: ProcurementState):
    return 'compliant' if state['is_compliant'] else 'reject'

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_api_purity)
graph.add_conditional_edges('validate', check_compliance, {'compliant': END, 'reject': END})
graph.set_entry_point('validate')