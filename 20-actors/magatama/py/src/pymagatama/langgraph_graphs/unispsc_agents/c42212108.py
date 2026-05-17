from typing import TypedDict
from langgraph.graph import StateGraph, END

class ToolSpecState(TypedDict):
    tool_type: str
    ergonomic_level: int
    is_validated: bool

def validate_ergonomics(state: ToolSpecState):
    state['is_validated'] = state['ergonomic_level'] >= 5
    return state

def route_by_validation(state: ToolSpecState):
    return 'valid' if state['is_validated'] else 'manual_review'

graph = StateGraph(ToolSpecState)
graph.add_node('validate', validate_ergonomics)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation, {'valid': END, 'manual_review': END})
graph.compile()