from typing import TypedDict
from langgraph.graph import StateGraph, END

class FastenerState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_specs(state: FastenerState):
    check = all(k in state['spec_data'] for k in ['material', 'standard'])
    return {'validation_passed': check}

def route_procurement(state: FastenerState):
    return 'validate' if not state['validation_passed'] else 'complete'

graph = StateGraph(FastenerState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()