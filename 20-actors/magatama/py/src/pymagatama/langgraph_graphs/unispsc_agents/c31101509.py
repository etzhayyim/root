from typing import TypedDict
from langgraph.graph import StateGraph, END

class DieCastState(TypedDict):
    specs: dict
    inspection_passed: bool

def validate_tin_composition(state: DieCastState):
    composition = state['specs'].get('composition', {})
    # Logic for tin alloy purity validation
    state['inspection_passed'] = composition.get('sn_percentage', 0) > 90
    return state

def check_dimensions(state: DieCastState):
    # Simulate CAD dimension verification process
    return {'inspection_passed': state['inspection_passed'] and True}

graph = StateGraph(DieCastState)
graph.add_node('validate_composition', validate_tin_composition)
graph.add_node('check_dimensions', check_dimensions)
graph.add_edge('validate_composition', 'check_dimensions')
graph.add_edge('check_dimensions', END)
graph.set_entry_point('validate_composition')
graph = graph.compile()