from typing import TypedDict
from langgraph.graph import StateGraph, END

class ValveState(TypedDict):
    spec_data: dict
    validation_passed: bool
    error_log: list

def validate_specs(state: ValveState):
    required = ['pressure_rating', 'material']
    passed = all(k in state['spec_data'] for k in required)
    return {'validation_passed': passed}

def route_verification(state: ValveState):
    return 'process' if state['validation_passed'] else 'error'

graph = StateGraph(ValveState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
