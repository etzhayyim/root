from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity: float
    compliance_docs: list
    is_approved: bool

def validate_purity(state: ProcurementState):
    state['is_approved'] = state['purity'] >= 99.0
    return state

def check_compliance(state: ProcurementState):
    if 'CoA' in state['compliance_docs']:
        return {'is_approved': state['is_approved']}
    return {'is_approved': False}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_purity)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()