from typing import TypedDict
from langgraph.graph import StateGraph, END

class StickerState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_approved: bool

def validate_materials(state: StickerState):
    errors = []
    if 'AdhesiveType' not in state['spec_data']:
        errors.append('Missing Adhesive Specification')
    return {'validation_errors': errors}

def approval_check(state: StickerState):
    approved = len(state['validation_errors']) == 0
    return {'is_approved': approved}

graph = StateGraph(StickerState)
graph.add_node('validate', validate_materials)
graph.add_node('approve', approval_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()