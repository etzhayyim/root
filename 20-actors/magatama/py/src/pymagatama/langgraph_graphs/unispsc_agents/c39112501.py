from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LightingState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: LightingState):
    errors = []
    if state['spec_data'].get('luminous_flux', 0) < 500:
         errors.append('Insufficient luminous flux for professional use')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

graph = StateGraph(LightingState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
