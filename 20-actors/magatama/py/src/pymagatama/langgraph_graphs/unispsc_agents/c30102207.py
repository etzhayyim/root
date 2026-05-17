from typing import TypedDict
from langgraph.graph import StateGraph, END

class MagnesiumState(TypedDict):
    purity: float
    thickness: float
    compliance_checked: bool

def validate_purity(state: MagnesiumState):
    state['compliance_checked'] = state['purity'] >= 99.9
    return state

def export_review(state: MagnesiumState):
    print('Flagging for dual-use export control review.')
    return state

builder = StateGraph(MagnesiumState)
builder.add_node('validate', validate_purity)
builder.add_node('export_check', export_review)
builder.set_entry_point('validate')
builder.add_edge('validate', 'export_check')
builder.add_edge('export_check', END)
graph = builder.compile()