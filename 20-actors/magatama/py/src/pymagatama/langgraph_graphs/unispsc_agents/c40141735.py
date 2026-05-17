from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class FunnelState(TypedDict):
    material: str
    diameter: float
    spec_check: bool

def validate_funnel_spec(state: FunnelState):
    # Business logic for specific funnel quality control
    if state['diameter'] <= 0:
        return {'spec_check': False}
    return {'spec_check': True}

graph = StateGraph(FunnelState)
graph.add_node('validate', validate_funnel_spec)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()