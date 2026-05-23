from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    material_spec: str
    sterility_check: bool
    compliance_ok: bool

def validate_materials(state: ProcurementState):
    state['compliance_ok'] = 'Latex' not in state['material_spec']
    return state

def verify_sterility(state: ProcurementState):
    state['sterility_check'] = True
    return state

builder = StateGraph(ProcurementState)
builder.add_node('validate', validate_materials)
builder.add_node('sterility', verify_sterility)
builder.add_edge('validate', 'sterility')
builder.add_edge('sterility', END)
builder.set_entry_point('validate')
graph = builder.compile()
