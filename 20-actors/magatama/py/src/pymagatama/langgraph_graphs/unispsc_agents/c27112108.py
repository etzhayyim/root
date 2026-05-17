from typing import TypedDict
from langgraph.graph import StateGraph, END

class ToolSpecState(TypedDict):
    spec_data: dict
    is_verified: bool

def validate_specs(state: ToolSpecState):
    hardness = state['spec_data'].get('hardness', 0)
    state['is_verified'] = hardness >= 45
    return state

graph = StateGraph(ToolSpecState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()