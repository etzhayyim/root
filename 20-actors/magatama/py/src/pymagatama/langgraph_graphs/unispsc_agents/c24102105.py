from typing import TypedDict
from langgraph.graph import StateGraph, END

class PalletizerState(TypedDict):
    capacity: float
    safety_verified: bool
    integration_status: str

def validate_specs(state: PalletizerState):
    if state['capacity'] > 0:
        return {'safety_verified': True}
    return {'safety_verified': False}

def check_integration(state: PalletizerState):
    return {'integration_status': 'COMPATIBLE'}

graph = StateGraph(PalletizerState)
graph.add_node('validate', validate_specs)
graph.add_node('integrate', check_integration)
graph.add_edge('validate', 'integrate')
graph.add_edge('integrate', END)
graph.set_entry_point('validate')
graph = graph.compile()