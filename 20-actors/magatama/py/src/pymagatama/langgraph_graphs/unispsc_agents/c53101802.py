from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class GarmentState(TypedDict):
    specifications: dict
    validation_passed: bool
    errors: List[str]

def validate_materials(state: GarmentState):
    # Business logic for checking textile quality standards
    state['validation_passed'] = 'Material Composition' in state['specifications']
    if not state['validation_passed']: state['errors'].append('Missing material specs')
    return state

def check_compliance(state: GarmentState):
    # Check for safety and chemical compliance (e.g. Oeko-Tex)
    return state

builder = StateGraph(GarmentState)
builder.add_node('validate', validate_materials)
builder.add_node('compliance', check_compliance)
builder.add_edge('validate', 'compliance')
builder.add_edge('compliance', END)
builder.set_entry_point('validate')
graph = builder.compile()