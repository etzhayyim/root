from typing import TypedDict
from langgraph.graph import StateGraph, END

class ToolState(TypedDict):
    tool_type: str
    thrust_ratio: int
    is_validated: bool

def validate_tool(state: ToolState):
    state['is_validated'] = state['thrust_ratio'] >= 12
    return state

graph = StateGraph(ToolState)
graph.add_node('validate', validate_tool)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
