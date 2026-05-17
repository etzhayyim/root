from typing import TypedDict
from langgraph.graph import StateGraph, END

class SkateState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_approved: bool

def validate_specs(state: SkateState):
    errors = []
    if not state['spec_data'].get('blade_material_grade'):
        errors.append('Missing blade material')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

graph = StateGraph(SkateState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()