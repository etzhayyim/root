from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BilletState(TypedDict):
    specifications: dict
    compliance_check: bool
    approved: bool

def validate_quality(state: BilletState):
    # Simulate chemical property validation
    carbon_content = state['specifications'].get('carbon', 0)
    state['compliance_check'] = 0.1 < carbon_content < 0.5
    return state

def check_certification(state: BilletState):
    state['approved'] = state['compliance_check'] and 'mill_cert' in state['specifications']
    return state

graph = StateGraph(BilletState)
graph.add_node('validate', validate_quality)
graph.add_node('certify', check_certification)
graph.add_edge('validate', 'certify')
graph.add_edge('certify', END)
graph.set_entry_point('validate')
graph = graph.compile()
