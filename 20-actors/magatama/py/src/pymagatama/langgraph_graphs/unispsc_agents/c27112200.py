from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ToolSpecState(TypedDict):
    tool_type: str
    safety_standards: List[str]
    approved: bool

def validate_tools(state: ToolSpecState):
    required = ['ISO9001', 'SafetyTested']
    all_met = all(s in state['safety_standards'] for s in required)
    return {'approved': all_met}

graph = StateGraph(ToolSpecState)
graph.add_node('validate', validate_tools)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
