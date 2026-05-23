from typing import TypedDict
from langgraph.graph import StateGraph

class SanitarySpecState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_approved: bool

def validate_material(state: SanitarySpecState):
    errors = []
    if 'material' not in state['spec_data']:
        errors.append('Material missing')
    return {'validation_errors': errors}

def check_compliance(state: SanitarySpecState):
    approved = len(state['validation_errors']) == 0
    return {'is_approved': approved}

graph = StateGraph(SanitarySpecState)
graph.add_node('validate', validate_material)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.set_entry_point('validate')
graph.set_finish_point('compliance')
graph = graph.compile()
