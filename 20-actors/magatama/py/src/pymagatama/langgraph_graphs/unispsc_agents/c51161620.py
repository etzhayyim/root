from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity: float
    compliance_docs: bool
    is_approved: bool

def validate_purity(state: ProcurementState):
    state['is_approved'] = state['purity'] >= 99.0 and state['compliance_docs']
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_purity)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
