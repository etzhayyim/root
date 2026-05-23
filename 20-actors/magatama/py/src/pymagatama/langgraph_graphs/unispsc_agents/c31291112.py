from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RubberSpecState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_dimensions(state: RubberSpecState):
    errors = []
    if 'tolerance' not in state['spec_data']: errors.append('Missing tolerance data')
    return {'validation_errors': errors}

def check_material_compliance(state: RubberSpecState):
    return {'is_approved': len(state['validation_errors']) == 0}

builder = StateGraph(RubberSpecState)
builder.add_node('validate', validate_dimensions)
builder.add_node('compliance', check_material_compliance)
builder.add_edge('validate', 'compliance')
builder.add_edge('compliance', END)
builder.set_entry_point('validate')
graph = builder.compile()
