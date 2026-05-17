from typing import TypedDict
from langgraph.graph import StateGraph, END

class CableState(TypedDict):
    specifications: dict
    validation_passed: bool

def validate_cable_specs(state: CableState):
    specs = state['specifications']
    required = ['voltage', 'insulation', 'f_rating']
    validation = all(key in specs for key in required)
    return {'validation_passed': validation}

def route_by_validation(state: CableState):
    return 'valid' if state['validation_passed'] else 'invalid'

graph = StateGraph(CableState)
graph.add_node('validate', validate_cable_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation, {'valid': END, 'invalid': END})
graph.compile()