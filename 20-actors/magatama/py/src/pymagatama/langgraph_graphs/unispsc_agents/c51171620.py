from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity_level: float
    gmp_valid: bool
    compliance_docs: List[str]
    approved: bool

def validate_purity(state: ProcurementState):
    state['approved'] = state['purity_level'] >= 99.0 and state['gmp_valid']
    return state

def check_documentation(state: ProcurementState):
    state['approved'] = state['approved'] and len(state['compliance_docs']) >= 3
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_purity)
graph.add_node('docs', check_documentation)
graph.set_entry_point('validate')
graph.add_edge('validate', 'docs')
graph.add_edge('docs', END)
graph = graph.compile()