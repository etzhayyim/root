from typing import TypedDict, Annotated, List, Dict
from langgraph.graph import StateGraph, END

class ResinState(TypedDict):
    batch_id: str
    specs: Dict[str, float]
    status: str
    log: List[str]

def validate_specs(state: ResinState) -> ResinState:
    s = state['specs']
    if s.get('tensile_strength_mpa', 0) > 500:
        state['status'] = 'PASSED_STRUCTURAL'
    else:
        state['status'] = 'FAILED_STRUCTURAL'
    state['log'].append('Validated tensile strength')
    return state

def check_compliance(state: ResinState) -> ResinState:
    if state['status'] == 'PASSED_STRUCTURAL':
        state['status'] = 'COMPLIANCE_APPROVED'
    state['log'].append('Verified export compliance')
    return state

builder = StateGraph(ResinState)
builder.add_node('validate', validate_specs)
builder.add_node('compliance', check_compliance)
builder.set_entry_point('validate')
builder.add_edge('validate', 'compliance')
builder.add_edge('compliance', END)
graph = builder.compile()
