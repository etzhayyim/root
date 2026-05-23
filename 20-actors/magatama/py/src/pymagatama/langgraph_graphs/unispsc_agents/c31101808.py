from typing import TypedDict
from langgraph.graph import StateGraph, END

class CastingState(TypedDict):
    spec_doc: str
    validation_score: float
    nondestructive_test_results: dict

def validate_material(state: CastingState):
    # Simulate material compliance check for Titanium grade
    state['validation_score'] = 1.0 if 'Grade 5' in state['spec_doc'] else 0.0
    return state

def check_ndt_specs(state: CastingState):
    # Simulate NDT verification logic
    state['nondestructive_test_results'] = {'ultrasonic': 'PASS', 'xray': 'PASS'}
    return state

graph = StateGraph(CastingState)
graph.add_node('validate', validate_material)
graph.add_node('ndt_check', check_ndt_specs)
graph.add_edge('validate', 'ndt_check')
graph.add_edge('ndt_check', END)
graph.set_entry_point('validate')
graph = graph.compile()
