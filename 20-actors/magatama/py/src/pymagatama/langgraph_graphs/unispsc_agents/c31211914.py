from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class AirbrushState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_approved: bool

def validate_specs(state: AirbrushState):
    errors = []
    if state['specs'].get('nozzle_diameter', 0) <= 0:
        errors.append('Invalid nozzle diameter.')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

graph = StateGraph(AirbrushState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()