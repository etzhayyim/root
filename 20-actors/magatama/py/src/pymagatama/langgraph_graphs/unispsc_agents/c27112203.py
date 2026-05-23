from typing import TypedDict
from langgraph.graph import StateGraph, END

class ToolState(TypedDict):
    tool_type: str
    blade_integrity: bool
    safety_check: bool

def validate_tool(state: ToolState):
    state['blade_integrity'] = True
    return 'safety_check'

def check_safety(state: ToolState):
    state['safety_check'] = True
    return END

graph = StateGraph(ToolState)
graph.add_node('validate', validate_tool)
graph.add_node('safety', check_safety)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
app = graph.compile()
