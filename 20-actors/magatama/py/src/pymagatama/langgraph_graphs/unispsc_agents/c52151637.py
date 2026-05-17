from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CarvingToolState(TypedDict):
    tool_items: List[str]
    validation_passed: bool
    safety_check: str

def validate_tools(state: CarvingToolState):
    passed = len(state['tool_items']) >= 3
    return {'validation_passed': passed, 'safety_check': 'complete'}

graph = StateGraph(CarvingToolState)
graph.add_node('validate', validate_tools)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()