from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class RareEarthState(TypedDict):
    material_code: str
    purity_level: float
    compliance_checks: List[str]
    validation_status: str

def validate_material_purity(state: RareEarthState) -> RareEarthState:
    if state['purity_level'] >= 99.9:
        state['validation_status'] = 'CERTIFIED_HIGH_GRADE'
    else:
        state['validation_status'] = 'REJECTED_LOW_GRADE'
    return state

def run_compliance_audit(state: RareEarthState) -> RareEarthState:
    state['compliance_checks'].append('EXPORT_CONTROL_VERIFIED')
    return state

builder = StateGraph(RareEarthState)
builder.add_node('validate', validate_material_purity)
builder.add_node('compliance', run_compliance_audit)
builder.add_edge('validate', 'compliance')
builder.add_edge('compliance', END)
builder.set_entry_point('validate')
graph = builder.compile()