from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class GeologyToolState(TypedDict):
    tool_type: str
    specs: dict
    validation_passed: bool

def validate_tool_specs(state: GeologyToolState):
    hardness = state['specs'].get('hardness', 0)
    state['validation_passed'] = hardness >= 50
    return state

def route_procurement(state: GeologyToolState):
    return 'process' if state['validation_passed'] else 'reject'

graph = StateGraph(GeologyToolState)
graph.add_node('validate', validate_tool_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
