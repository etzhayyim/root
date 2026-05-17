from typing import TypedDict
from langgraph.graph import StateGraph, END

class ValveState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_specs(state: ValveState):
    required = ['pressure_rating_mpa', 'material_composition']
    passed = all(k in state['spec_data'] for k in required)
    return {'validation_passed': passed}

def route_by_validation(state: ValveState):
    return 'process' if state['validation_passed'] else 'reject'

graph = StateGraph(ValveState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation, {'process': END, 'reject': END})