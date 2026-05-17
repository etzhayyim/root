from langgraph.graph import StateGraph, END
from typing import TypedDict

class GasOutletState(TypedDict):
    part_number: str
    gas_type: str
    compliance_docs: bool
    is_verified: bool

def validate_compliance(state: GasOutletState):
    # Simulate regulatory validation for critical medical equipment
    state['is_verified'] = state['compliance_docs'] and state['gas_type'] in ['Oxygen', 'Vacuum', 'Air']
    return state

def route_verification(state: GasOutletState):
    return 'verified' if state['is_verified'] else 'failed'

graph = StateGraph(GasOutletState)
graph.add_node('validate', validate_compliance)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()