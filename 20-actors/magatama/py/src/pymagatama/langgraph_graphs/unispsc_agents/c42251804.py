from typing import TypedDict
from langgraph.graph import StateGraph, END

class RehabCartState(TypedDict):
    spec_data: dict
    validation_results: list
    is_approved: bool

def validate_load_capacity(state: RehabCartState):
    capacity = state['spec_data'].get('weight_capacity_kg', 0)
    state['validation_results'].append('Capacity validated' if capacity > 0 else 'Capacity audit failed')
    return state

def check_compliance(state: RehabCartState):
    certified = state['spec_data'].get('iso_13485', False)
    state['is_approved'] = certified
    return state

graph = StateGraph(RehabCartState)
graph.add_node('validate_specs', validate_load_capacity)
graph.add_node('check_compliance', check_compliance)
graph.set_entry_point('validate_specs')
graph.add_edge('validate_specs', 'check_compliance')
graph.add_edge('check_compliance', END)
graph = graph.compile()
