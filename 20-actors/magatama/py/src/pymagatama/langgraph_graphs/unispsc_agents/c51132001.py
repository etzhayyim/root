from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity: float
    gmp_status: bool
    is_approved: bool

def validate_purity(state: ProcurementState):
    state['is_approved'] = state['purity'] >= 99.0
    return state

def check_gmp(state: ProcurementState):
    if not state.get('gmp_status'):
        state['is_approved'] = False
    return state

builder = StateGraph(ProcurementState)
builder.add_node('validate_purity', validate_purity)
builder.add_node('check_gmp', check_gmp)
builder.set_entry_point('validate_purity')
builder.add_edge('validate_purity', 'check_gmp')
builder.add_edge('check_gmp', END)
graph = builder.compile()