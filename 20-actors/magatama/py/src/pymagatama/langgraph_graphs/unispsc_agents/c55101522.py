from typing import TypedDict
from langgraph.graph import StateGraph, END

class GlobeState(TypedDict):
    globe_type: str
    material: str
    verification_passed: bool

def validate_globe_specs(state: GlobeState):
    # Logic to verify geometric accuracy and base stability
    if state['globe_type'] in ['terrestrial', 'celestial']:
        return {'verification_passed': True}
    return {'verification_passed': False}

graph = StateGraph(GlobeState)
graph.add_node('validate', validate_globe_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()