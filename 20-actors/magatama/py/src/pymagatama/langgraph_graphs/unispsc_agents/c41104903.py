from typing import TypedDict
from langgraph.graph import StateGraph, END

class FiltrationState(TypedDict):
    specs: dict
    validation_passed: bool

def validate_specs(state: FiltrationState):
    required = ['membrane_material', 'pore_size_rating']
    passed = all(k in state['specs'] for k in required)
    return {'validation_passed': passed}

def route_by_validation(state: FiltrationState):
    return 'process' if state['validation_passed'] else END

builder = StateGraph(FiltrationState)
builder.add_node('validate', validate_specs)
builder.add_node('process', lambda s: s)
builder.set_entry_point('validate')
builder.add_conditional_edges('validate', route_by_validation)
builder.add_edge('process', END)
graph = builder.compile()
