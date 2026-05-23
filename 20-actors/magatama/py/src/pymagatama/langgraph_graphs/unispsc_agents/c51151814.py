from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity: float
    compliance_docs: bool
    approved: bool

def validate_purity(state: ProcurementState):
    state['approved'] = state['purity'] >= 99.0
    return state

def verify_compliance(state: ProcurementState):
    if not state.get('compliance_docs'):
        state['approved'] = False
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('verify_compliance', verify_compliance)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'verify_compliance')
graph.add_edge('verify_compliance', END)
graph = graph.compile()
