from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    purity: float
    has_sds: bool
    is_approved: bool

def validate_quality(state: ChemicalState):
    state['is_approved'] = state['purity'] >= 99.0 and state['has_sds']
    return state

builder = StateGraph(ChemicalState)
builder.add_node('validate', validate_quality)
builder.set_entry_point('validate')
builder.add_edge('validate', END)
graph = builder.compile()