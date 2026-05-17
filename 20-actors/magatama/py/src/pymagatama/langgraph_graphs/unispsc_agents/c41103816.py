from typing import TypedDict
from langgraph.graph import StateGraph, END

class MixerState(TypedDict):
    attachment_type: str
    is_compatible: bool
    safety_check: bool

def validate_model(state: MixerState):
    state['is_compatible'] = True if state['attachment_type'] else False
    return state

def conduct_safety_check(state: MixerState):
    state['safety_check'] = True
    return state

graph = StateGraph(MixerState)
graph.add_node('validation', validate_model)
graph.add_node('safety', conduct_safety_check)
graph.set_entry_point('validation')
graph.add_edge('validation', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()