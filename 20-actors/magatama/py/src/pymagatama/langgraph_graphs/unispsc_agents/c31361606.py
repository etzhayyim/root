from typing import TypedDict
from langgraph.graph import StateGraph, END

class AssemblyState(TypedDict):
    material_specs: dict
    weld_integrity: float
    status: str

def validate_welding(state: AssemblyState) -> AssemblyState:
    if state['weld_integrity'] >= 0.95:
        state['status'] = 'APPROVED'
    else:
        state['status'] = 'REJECTED'
    return state

builder = StateGraph(AssemblyState)
builder.add_node('weld_validation', validate_welding)
builder.set_entry_point('weld_validation')
builder.add_edge('weld_validation', END)
graph = builder.compile()
