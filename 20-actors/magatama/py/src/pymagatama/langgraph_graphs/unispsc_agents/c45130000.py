from typing import TypedDict
from langgraph.graph import StateGraph, END

class MediaState(TypedDict):
    media_type: str
    capacity: int
    is_verified: bool

def validate_media(state: MediaState):
    state['is_verified'] = state['capacity'] > 0
    return state

def check_compliance(state: MediaState):
    return 'compliant' if state['is_verified'] else 'non-compliant'

graph = StateGraph(MediaState)
graph.add_node('validate', validate_media)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
compile_graph = graph.compile()