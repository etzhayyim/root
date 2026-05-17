from typing import TypedDict
from langgraph.graph import StateGraph, END

class WineSpecState(TypedDict):
    alcohol_content: float
    safety_clearance: bool
    is_approved: bool

def validate_quality(state: WineSpecState):
    # Business logic for cooking wine safety check
    state['is_approved'] = 0.5 <= state['alcohol_content'] <= 15.0 and state['safety_clearance']
    return state

graph = StateGraph(WineSpecState)
graph.add_node('validate', validate_quality)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()