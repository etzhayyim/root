from typing import TypedDict
from langgraph.graph import StateGraph, END

class RopeState(TypedDict):
    spec_data: dict
    approved: bool

def validate_rope_specs(state: RopeState):
    diameter = state['spec_data'].get('diameter_mm', 0)
    state['approved'] = diameter > 0 and 'tensile_test_certificate' in state['spec_data']
    return state

def check_origin(state: RopeState):
    return state

graph = StateGraph(RopeState)
graph.add_node('validate', validate_rope_specs)
graph.add_node('compliance', check_origin)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
