from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class AssemblyState(TypedDict):
    specifications: dict
    validation_passed: bool
    errors: List[str]

def validate_copper_specs(state: AssemblyState):
    specs = state['specifications']
    errors = []
    if specs.get('tensile_strength', 0) < 200:
        errors.append('Tensile strength below industrial minimum')
    return {'validation_passed': len(errors) == 0, 'errors': errors}

def route_by_validation(state: AssemblyState):
    return 'valid' if state['validation_passed'] else 'invalid'

graph = StateGraph(AssemblyState)
graph.add_node('validate', validate_copper_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()