from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CameraAccessoryState(TypedDict):
    item_name: str
    compatibility: str
    quality_score: float
    approved: bool

def validate_compatibility(state: CameraAccessoryState):
    # Business logic for compatibility check
    state['approved'] = 'mount' in state['compatibility'].lower()
    return state

def verify_quality(state: CameraAccessoryState):
    # Inspection logic
    state['quality_score'] = 1.0 if state['approved'] else 0.0
    return state

graph = StateGraph(CameraAccessoryState)
graph.add_node('validate', validate_compatibility)
graph.add_node('verify', verify_quality)
graph.set_entry_point('validate')
graph.add_edge('validate', 'verify')
graph.add_edge('verify', END)
graph = graph.compile()