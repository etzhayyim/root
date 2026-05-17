from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PiracetamState(TypedDict):
    purity: float
    gmp_certified: bool
    compliance_docs: List[str]
    approved: bool

def validate_quality(state: PiracetamState):
    state['approved'] = state['purity'] >= 99.0 and state['gmp_certified']
    return state

builder = StateGraph(PiracetamState)
builder.add_node('quality_check', validate_quality)
builder.set_entry_point('quality_check')
builder.add_edge('quality_check', END)
graph = builder.compile()