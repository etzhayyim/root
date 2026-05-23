from typing import TypedDict
from langgraph.graph import StateGraph, END

class ToolState(TypedDict):
    tool_type: str
    blade_hardness: int
    safety_verified: bool

def validate_tool(state: ToolState):
    if state['blade_hardness'] < 50:
        return {'safety_verified': False}
    return {'safety_verified': True}

def final_check(state: ToolState):
    return 'passed' if state['safety_verified'] else 'rejected'

graph = StateGraph(ToolState)
graph.add_node('validate', validate_tool)
graph.add_node('final', final_check)
graph.add_edge('validate', 'final')
graph.add_edge('final', END)
graph.set_entry_point('validate')
graph = graph.compile()
