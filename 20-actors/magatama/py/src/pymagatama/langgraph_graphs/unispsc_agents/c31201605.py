from typing import TypedDict
from langgraph.graph import StateGraph, END

class PuttyState(TypedDict):
    material_type: str
    curing_required: bool
    compliance_docs: list[str]
    validation_passed: bool

def validate_materials(state: PuttyState):
    # Business logic for putty chemical safety checks
    state['validation_passed'] = 'msds' in state['compliance_docs'] and state['material_type'] != 'restricted'
    return state

def route_by_type(state: PuttyState):
    return 'process_curing' if state['curing_required'] else END

builder = StateGraph(PuttyState)
builder.add_node('validate', validate_materials)
builder.set_entry_point('validate')
builder.add_edge('validate', END)
graph = builder.compile()
