from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class SolventState(TypedDict):
    purity_level: float
    safety_verified: bool
    compliance_tags: List[str]
    steps: List[str]

def validate_purity(state: SolventState) -> SolventState:
    if state['purity_level'] >= 99.9:
        state['steps'].append('Purity validated')
    return state

def check_compliance(state: SolventState) -> SolventState:
    if 'dangerous-goods' in state['compliance_tags']:
        state['safety_verified'] = True
        state['steps'].append('Compliance verified')
    return state

builder = StateGraph(SolventState)
builder.add_node('validate', validate_purity)
builder.add_node('compliance', check_compliance)
builder.add_edge('validate', 'compliance')
builder.add_edge('compliance', END)
builder.set_entry_point('validate')
graph = builder.compile()
