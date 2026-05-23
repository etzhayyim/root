import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END

class KickingTeeState(TypedDict):
    spec_data: dict
    validation_errors: Annotated[list, operator.add]
    is_approved: bool

def validate_material(state: KickingTeeState):
    errors = []
    if 'material' not in state['spec_data']:
        errors.append('Material missing')
    return {'validation_errors': errors}

def approve_procurement(state: KickingTeeState):
    is_approved = len(state['validation_errors']) == 0
    return {'is_approved': is_approved}

builder = StateGraph(KickingTeeState)
builder.add_node('validate', validate_material)
builder.add_node('approve', approve_procurement)
builder.add_edge('validate', 'approve')
builder.add_edge('approve', END)
builder.set_entry_point('validate')
graph = builder.compile()
