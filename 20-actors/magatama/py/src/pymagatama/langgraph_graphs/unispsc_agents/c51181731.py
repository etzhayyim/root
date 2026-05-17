from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity: float
    compliant: bool
    document_path: str

def validate_purity(state: ProcurementState):
    state['compliant'] = state['purity'] >= 99.0
    return state

def check_compliance(state: ProcurementState):
    return 'compliant_node' if state['compliant'] else 'reject_node'

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_purity)
graph.add_node('compliant_node', lambda s: s)
graph.add_node('reject_node', lambda s: s)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', check_compliance)
graph.add_edge('compliant_node', END)
graph.add_edge('reject_node', END)

graph = graph.compile()