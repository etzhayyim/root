from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmacyState(TypedDict):
    chemical_name: str
    purity_level: float
    compliance_docs: bool
    approved: bool

def validate_purity(state: PharmacyState):
    state['approved'] = state['purity_level'] >= 99.0
    return state

def check_documentation(state: PharmacyState):
    if state['approved'] and state['compliance_docs']:
        return 'final'
    return 'reject'

graph = StateGraph(PharmacyState)
graph.add_node('validate', validate_purity)
graph.add_node('verify_docs', check_documentation)
graph.set_entry_point('validate')
graph.add_edge('validate', 'verify_docs')
graph.add_edge('verify_docs', END)