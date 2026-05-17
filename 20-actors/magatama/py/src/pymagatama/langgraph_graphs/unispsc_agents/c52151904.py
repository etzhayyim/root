from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RoastingPanState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_material(state: RoastingPanState):
    errors = []
    if state['spec_data'].get('material') not in ['stainless_steel', 'cast_iron', 'enamelled_steel']:
        errors.append('Invalid or unsupported material type.')
    return {'validation_errors': errors}

def check_compliance(state: RoastingPanState):
    is_valid = len(state['validation_errors']) == 0
    return {'approved': is_valid}

graph = StateGraph(RoastingPanState)
graph.add_node('validate', validate_material)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()