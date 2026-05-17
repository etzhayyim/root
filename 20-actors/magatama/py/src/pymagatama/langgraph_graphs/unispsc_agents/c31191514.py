from typing import TypedDict
from langgraph.graph import StateGraph, END

class State(TypedDict):
    media_type: str
    grit_size: int
    is_approved: bool

def validate_media(state: State):
    if state['grit_size'] > 0 and state['media_type']:
        return {'is_approved': True}
    return {'is_approved': False}

graph = StateGraph(State)
graph.add_node('validate', validate_media)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()