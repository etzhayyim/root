from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MowerAttachmentState(TypedDict):
    specs: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: MowerAttachmentState):
    errors = []
    if not state['specs'].get('blade_material'):
        errors.append('Missing mandatory blade material spec')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

def route_by_validation(state: MowerAttachmentState):
    return 'approved' if state['approved'] else 'rejected'

graph = StateGraph(MowerAttachmentState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()