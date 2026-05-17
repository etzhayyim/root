from typing import TypedDict
from langgraph.graph import StateGraph, END

class SolarReelState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_dimensions(state: SolarReelState):
    width = state['spec_data'].get('width', 0)
    state['is_compliant'] = width > 0 and width < 10
    if state['is_compliant']: return 'approved'
    return 'flagged'

def finalize_order(state: SolarReelState):
    return state

graph = StateGraph(SolarReelState)
graph.add_node('validate', validate_dimensions)
graph.add_node('final', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'final')
graph.add_edge('final', END)
graph = graph.compile()