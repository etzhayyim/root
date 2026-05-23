from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class RawMaterialState(TypedDict):
    material_id: str
    sustainability_certified: bool
    inspection_passed: bool
    traceability_data: str
    processing_steps: List[str]

def validate_certification(state: RawMaterialState) -> RawMaterialState:
    state['sustainability_certified'] = True
    state['processing_steps'].append('certification_verified')
    return state

def perform_inspection(state: RawMaterialState) -> RawMaterialState:
    state['inspection_passed'] = True
    state['processing_steps'].append('material_inspected')
    return state

builder = StateGraph(RawMaterialState)
builder.add_node('certify', validate_certification)
builder.add_node('inspect', perform_inspection)
builder.add_edge('certify', 'inspect')
builder.add_edge('inspect', END)
builder.set_entry_point('certify')
graph = builder.compile()
