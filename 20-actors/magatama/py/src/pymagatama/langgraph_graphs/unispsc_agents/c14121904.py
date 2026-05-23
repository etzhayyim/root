from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class PackagingState(TypedDict):
    material_type: str
    spec_compliance: bool
    validation_log: List[str]

def validate_material(state: PackagingState) -> PackagingState:
    if state['material_type'] == 'kraft':
        state['spec_compliance'] = True
        state['validation_log'].append('Kraft material validated.')
    else:
        state['spec_compliance'] = False
        state['validation_log'].append('Invalid material type.')
    return state

def run_compliance_check(state: PackagingState) -> PackagingState:
    if state['spec_compliance']:
        state['validation_log'].append('Procurement standards met.')
    return state

builder = StateGraph(PackagingState)
builder.add_node('validate', validate_material)
builder.add_node('compliance', run_compliance_check)
builder.set_entry_point('validate')
builder.add_edge('validate', 'compliance')
builder.add_edge('compliance', END)
graph = builder.compile()
