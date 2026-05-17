from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class BulletinState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_materials(state: BulletinState):
    errors = []
    if not state['spec_data'].get('safety_cert'):
        errors.append('Missing safety certification for classroom materials.')
    return {'validation_errors': errors}

def check_compliance(state: BulletinState):
    is_valid = len(state['validation_errors']) == 0
    return {'approved': is_valid}

graph = StateGraph(BulletinState)
graph.add_node('validate', validate_materials)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()