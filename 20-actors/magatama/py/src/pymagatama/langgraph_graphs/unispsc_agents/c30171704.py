from typing import TypedDict
from langgraph.graph import StateGraph, END

class GlassState(TypedDict):
    lead_equivalent: float
    dimensions: tuple
    compliance_ok: bool

def validate_shielding(state: GlassState):
    state['compliance_ok'] = state['lead_equivalent'] >= 2.0
    return state

def check_dimensions(state: GlassState):
    return state

graph = StateGraph(GlassState)
graph.add_node('validate', validate_shielding)
graph.add_node('specs', check_dimensions)
graph.set_entry_point('validate')
graph.add_edge('validate', 'specs')
graph.add_edge('specs', END)
graph = graph.compile()
