from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class SolventState(TypedDict):
    purity_level: float
    safety_clearance: bool
    compliance_docs: list

def validate_purity(state: SolventState) -> SolventState:
    if state['purity_level'] < 99.9:
        raise ValueError('Purity below industrial threshold')
    return state

def check_compliance(state: SolventState) -> SolventState:
    state['safety_clearance'] = len(state['compliance_docs']) >= 3
    return state

builder = StateGraph(SolventState)
builder.add_node('validate', validate_purity)
builder.add_node('compliance', check_compliance)
builder.add_edge('validate', 'compliance')
builder.add_edge('compliance', END)
builder.set_entry_point('validate')
graph = builder.compile()