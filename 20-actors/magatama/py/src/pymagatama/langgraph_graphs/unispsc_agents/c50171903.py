from typing import TypedDict
from langgraph.graph import StateGraph, END

class OliveState(TypedDict):
    quality_score: float
    origin_verified: bool
    is_safe: bool

def validate_olive_quality(state: OliveState):
    state['is_safe'] = state['quality_score'] > 0.8 and state['origin_verified']
    return state

builder = StateGraph(OliveState)
builder.add_node('qc', validate_olive_quality)
builder.set_entry_point('qc')
builder.add_edge('qc', END)
graph = builder.compile()