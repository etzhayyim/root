from typing import TypedDict
from langgraph.graph import StateGraph, END

class RelayState(TypedDict):
    voltage_rating: float
    current_capacity: float
    compliance_docs: list
    is_verified: bool

def validate_specs(state: RelayState):
    state['is_verified'] = state['voltage_rating'] > 0 and state['current_capacity'] > 0
    return state

def check_compliance(state: RelayState):
    if 'ISO' in str(state['compliance_docs']):
        state['is_verified'] = True
    return state

graph = StateGraph(RelayState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
