from typing import TypedDict
from langgraph.graph import StateGraph, END

class PindololState(TypedDict):
    purity: float
    compliance_docs: bool
    approved: bool

def validate_purity(state: PindololState):
    state['approved'] = state['purity'] >= 99.0
    return state

def check_compliance(state: PindololState):
    return state

builder = StateGraph(PindololState)
builder.add_node('validate', validate_purity)
builder.add_node('compliance', check_compliance)
builder.add_edge('validate', 'compliance')
builder.add_edge('compliance', END)
builder.set_entry_point('validate')
graph = builder.compile()