from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class NuclearState(TypedDict):
    enrichment: float
    safety_clearance: bool
    is_compliant: bool

def validate_enrichment(state: NuclearState) -> NuclearState:
    state['is_compliant'] = state['enrichment'] < 20.0
    return state

def check_security_protocol(state: NuclearState) -> NuclearState:
    state['safety_clearance'] = True
    return state

graph = StateGraph(NuclearState)
graph.add_node('validate', validate_enrichment)
graph.add_node('security', check_security_protocol)
graph.add_edge('validate', 'security')
graph.add_edge('security', END)
graph.set_entry_point('validate')
graph = graph.compile()
