from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ViseState(TypedDict):
    pipe_diameter: float
    material: str
    validation_passed: bool
    errors: List[str]

def validate_specs(state: ViseState):
    errors = []
    if state['pipe_diameter'] <= 0:
        errors.append('Invalid pipe diameter')
    return {'validation_passed': len(errors) == 0, 'errors': errors}

def route_by_validation(state: ViseState):
    return 'validate' if not state.get('validation_passed') else END

graph = StateGraph(ViseState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()