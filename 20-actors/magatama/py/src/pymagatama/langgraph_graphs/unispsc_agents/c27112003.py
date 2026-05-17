from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RakeProcurementState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_approved: bool

def validate_specs(state: RakeProcurementState):
    errors = []
    if not state['specs'].get('head_material'):
        errors.append('Head material is missing.')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

def route_verification(state: RakeProcurementState):
    return 'approved' if state['is_approved'] else 'rejected'

graph = StateGraph(RakeProcurementState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
app = graph.compile()