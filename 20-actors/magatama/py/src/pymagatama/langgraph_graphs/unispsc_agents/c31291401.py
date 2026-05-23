from typing import TypedDict
from langgraph.graph import StateGraph, END

class ExtrusionState(TypedDict):
    specs: dict
    validation_passed: bool

def validate_extrusion(state: ExtrusionState):
    # Simulate CAD and tolerance check
    required = ['alloy', 'tolerance']
    passed = all(k in state['specs'] for k in required)
    return {'validation_passed': passed}

graph = StateGraph(ExtrusionState)
graph.add_node('validate', validate_extrusion)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
