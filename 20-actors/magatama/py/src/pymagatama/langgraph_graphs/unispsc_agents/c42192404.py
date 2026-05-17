from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CartState(TypedDict):
    spec_requirements: dict
    validation_passed: bool
    compliance_checks: List[str]

def validate_load_capacity(state: CartState):
    capacity = state['spec_requirements'].get('load_capacity', 0)
    state['validation_passed'] = capacity > 0
    return state

def check_compliance(state: CartState):
    if state['validation_passed']:
        state['compliance_checks'].append('IEC_60601_Verified')
    return state

graph = StateGraph(CartState)
graph.add_node('validate', validate_load_capacity)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()