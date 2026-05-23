from typing import TypedDict
from langgraph.graph import StateGraph, END

class GlowPaperState(TypedDict):
    luminance_val: float
    duration_min: int
    is_compliant: bool

def validate_luminance(state: GlowPaperState):
    state['is_compliant'] = state['luminance_val'] > 5.0 and state['duration_min'] >= 60
    return state

workflow = StateGraph(GlowPaperState)
workflow.add_node('validate', validate_luminance)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
