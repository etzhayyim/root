from typing import TypedDict
from langgraph.graph import StateGraph, END

class DentalProductState(TypedDict):
    product_id: str
    compliance_docs: list
    is_approved: bool

def validate_compliance(state: DentalProductState):
    required = {'sterility', 'iso_biocompatibility'}
    state['is_approved'] = all(doc in state['compliance_docs'] for doc in required)
    return state

def check_expiry(state: DentalProductState):
    return state

graph = StateGraph(DentalProductState)
graph.add_node('validate', validate_compliance)
graph.add_node('expiry', check_expiry)
graph.set_entry_point('validate')
graph.add_edge('validate', 'expiry')
graph.add_edge('expiry', END)
graph = graph.compile()