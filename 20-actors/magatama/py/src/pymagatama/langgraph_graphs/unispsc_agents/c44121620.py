from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    material: str
    size: str
    is_anti_static: bool
    approved: bool

def validate_material(state: ProcurementState) -> ProcurementState:
    state['approved'] = state['material'] in ['latex', 'nitrile']
    return state

def check_compliance(state: ProcurementState) -> ProcurementState:
    if state.get('is_anti_static') and state['material'] != 'nitrile':
        state['approved'] = False
    return state

builder = StateGraph(ProcurementState)
builder.add_node('validate', validate_material)
builder.add_node('compliance', check_compliance)
builder.add_edge('validate', 'compliance')
builder.add_edge('compliance', END)
builder.set_entry_point('validate')
graph = builder.compile()
