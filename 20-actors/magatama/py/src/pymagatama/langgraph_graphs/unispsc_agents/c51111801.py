from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    product_name: str
    compliance_docs: list
    is_verified: bool

def validate_pharmaceutical(state: ProcurementState):
    # Business logic for pharmaceutical procurement verification
    verified = all(['GMP_cert' in d for d in state['compliance_docs']])
    return {'is_verified': verified}

def route_verification(state: ProcurementState):
    return 'verified' if state['is_verified'] else 'rejected'

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_pharmaceutical)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()
