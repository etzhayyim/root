from typing import TypedDict
from langgraph.graph import StateGraph, END

class ExtrusionState(TypedDict):
    part_specs: dict
    validation_passed: bool

def validate_dimensions(state: ExtrusionState):
    specs = state['part_specs']
    passed = 'tolerance' in specs and specs['tolerance'] <= 0.05
    return {'validation_passed': passed}

def structural_integrity_check(state: ExtrusionState):
    specs = state['part_specs']
    passed = state['validation_passed'] and 'yield_strength' in specs
    return {'validation_passed': passed}

graph = StateGraph(ExtrusionState)
graph.add_node('validate', validate_dimensions)
graph.add_node('integrity', structural_integrity_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'integrity')
graph.add_edge('integrity', END)
graph = graph.compile()