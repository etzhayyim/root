from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class GrapeState(TypedDict):
    batch_id: str
    quality_score: float
    safety_verified: bool

def validate_quality(state: GrapeState):
    state['quality_score'] = 0.95 if state['batch_id'] else 0.0
    return state

def check_safety(state: GrapeState):
    state['safety_verified'] = state['quality_score'] > 0.9
    return state

graph = StateGraph(GrapeState)
graph.add_node('validate', validate_quality)
graph.add_node('safety', check_safety)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()
