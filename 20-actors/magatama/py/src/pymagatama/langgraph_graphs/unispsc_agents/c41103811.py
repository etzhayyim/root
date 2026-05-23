from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ShakerState(TypedDict):
    specs: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: ShakerState):
    errors = []
    if not (0 < state['specs'].get('orbit_diameter_mm', 0) <= 50):
        errors.append('Invalid orbit diameter range')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

graph = StateGraph(ShakerState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
