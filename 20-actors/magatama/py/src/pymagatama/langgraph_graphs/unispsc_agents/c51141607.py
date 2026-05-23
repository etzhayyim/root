from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmaState(TypedDict):
    purity: float
    compliance_docs: bool
    is_approved: bool

def validate_purity(state: PharmaState):
    state['is_approved'] = state['purity'] >= 99.0
    return state

def check_docs(state: PharmaState):
    state['is_approved'] = state['is_approved'] and state['compliance_docs']
    return state

builder = StateGraph(PharmaState)
builder.add_node('validate_purity', validate_purity)
builder.add_node('check_docs', check_docs)
builder.set_entry_point('validate_purity')
builder.add_edge('validate_purity', 'check_docs')
builder.add_edge('check_docs', END)
graph = builder.compile()
