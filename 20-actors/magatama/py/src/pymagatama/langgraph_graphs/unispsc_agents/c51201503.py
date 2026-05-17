from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MMFProcurementState(TypedDict):
    purity: float
    gmp_valid: bool
    batch_report: str
    approved: bool

def validate_purity(state: MMFProcurementState):
    state['approved'] = state['purity'] >= 99.0
    return state

def check_compliance(state: MMFProcurementState):
    if not state['gmp_valid']:
        state['approved'] = False
    return state

graph = StateGraph(MMFProcurementState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_compliance', check_compliance)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_compliance')
graph.add_edge('check_compliance', END)
graph = graph.compile()