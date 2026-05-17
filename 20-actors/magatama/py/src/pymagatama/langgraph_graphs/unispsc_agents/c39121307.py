from typing import TypedDict
from langgraph.graph import StateGraph, END

class FloorBoxState(TypedDict):
    spec_data: dict
    approved: bool

def validate_load_capacity(state: FloorBoxState):
    load = state['spec_data'].get('load_rating', 0)
    state['approved'] = load >= 500
    return state

def check_compliance(state: FloorBoxState):
    is_compliant = state['spec_data'].get('ip_rating', 0) >= 44
    state['approved'] = state['approved'] and is_compliant
    return state

graph = StateGraph(FloorBoxState)
graph.add_node('validate', validate_load_capacity)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()