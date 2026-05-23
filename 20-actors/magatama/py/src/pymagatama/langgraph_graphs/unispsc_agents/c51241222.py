from typing import TypedDict
from langgraph.graph import StateGraph, END

class DimethiconeState(TypedDict):
    purity: float
    viscosity: int
    is_compliant: bool

def validate_quality(state: DimethiconeState):
    state['is_compliant'] = state['purity'] >= 99.0 and state['viscosity'] > 0
    return state

def approval_node(state: DimethiconeState):
    return state

builder = StateGraph(DimethiconeState)
builder.add_node('validate', validate_quality)
builder.add_node('approval', approval_node)
builder.add_edge('validate', 'approval')
builder.add_edge('approval', END)
builder.set_entry_point('validate')
graph = builder.compile()
