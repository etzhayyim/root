from typing import TypedDict
from langgraph.graph import StateGraph, END

class BannerState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_approved: bool

def validate_materials(state: BannerState):
    errors = []
    if not state['spec_data'].get('fire_retardant_certification'):
        errors.append('Missing mandatory fire safety certification')
    return {'validation_errors': errors}

def approve_banner(state: BannerState):
    is_approved = len(state['validation_errors']) == 0
    return {'is_approved': is_approved}

graph = StateGraph(BannerState)
graph.add_node('validate', validate_materials)
graph.add_node('approve', approve_banner)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
