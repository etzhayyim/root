from typing import TypedDict
from langgraph.graph import StateGraph, END

class MagnesiumState(TypedDict):
    purity: float
    compliant: bool

def validate_quality(state: MagnesiumState):
    state['compliant'] = state['purity'] >= 99.0
    return 'valid' if state['compliant'] else 'invalid'

workflow = StateGraph(MagnesiumState)
workflow.add_node('check', validate_quality)
workflow.add_edge('check', END)
graph = workflow.compile()