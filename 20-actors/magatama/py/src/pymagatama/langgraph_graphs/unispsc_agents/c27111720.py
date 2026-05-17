from typing import TypedDict
from langgraph.graph import StateGraph, END

class ToolState(TypedDict):
    tool_id: str
    spec_data: dict
    approved: bool

def validate_tap_wrench(state: ToolState):
    # Business logic for wrench validation
    hrc = state['spec_data'].get('hardness_hrc', 0)
    state['approved'] = 45 <= hrc <= 60
    return state

graph = StateGraph(ToolState)
graph.add_node('validate', validate_tap_wrench)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()