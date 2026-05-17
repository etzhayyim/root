from typing import TypedDict
from langgraph.graph import StateGraph, END

class ArtilleryState(TypedDict):
    specs: dict
    compliance_verified: bool
    export_approved: bool

def validate_specs(state: ArtilleryState) -> ArtilleryState:
    # Simulate CAD/Spec validation for defense hardware
    state['compliance_verified'] = 'ballistic_protection_level' in state['specs']
    return state

def verify_export(state: ArtilleryState) -> ArtilleryState:
    # Simulate regulatory check
    state['export_approved'] = True
    return state

graph = StateGraph(ArtilleryState)
graph.add_node('validate', validate_specs)
graph.add_node('export', verify_export)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export')
graph.add_edge('export', END)
graph = graph.compile()