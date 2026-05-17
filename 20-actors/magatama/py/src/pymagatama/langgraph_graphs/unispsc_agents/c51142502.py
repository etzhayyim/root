from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity: float
    gmp_certified: bool
    validation_passed: bool

def validate_purity(state: ProcurementState):
    state['validation_passed'] = state['purity'] >= 99.0
    return state

def check_compliance(state: ProcurementState):
    if not state.get('gmp_certified'):
        state['validation_passed'] = False
    return state

graph = StateGraph(ProcurementState)
graph.add_node('purity_check', validate_purity)
graph.add_node('compliance_check', check_compliance)
graph.set_entry_point('purity_check')
graph.add_edge('purity_check', 'compliance_check')
graph.add_edge('compliance_check', END)
graph = graph.compile()