from typing import TypedDict
from langgraph.graph import StateGraph, END

class ContentState(TypedDict):
    license_type: str
    file_format: str
    is_compliant: bool

def validate_format(state: ContentState) -> ContentState:
    supported = ['pdf', 'epub', 'mp3', 'aac']
    state['is_compliant'] = state['file_format'].lower() in supported
    return state

def check_licensing(state: ContentState) -> ContentState:
    if state['license_type'] not in ['perpetual', 'subscription']:
        state['is_compliant'] = False
    return state

graph = StateGraph(ContentState)
graph.add_node('validate_format', validate_format)
graph.add_node('check_licensing', check_licensing)
graph.set_entry_point('validate_format')
graph.add_edge('validate_format', 'check_licensing')
graph.add_edge('check_licensing', END)
graph = graph.compile()