from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ToolSpecState(TypedDict):
    material: str
    grit_level: int
    inspection_result: bool

def validate_spec(state: ToolSpecState):
    state['inspection_result'] = state['grit_level'] > 0
    return state

def check_quality(state: ToolSpecState):
    return 'approved' if state['inspection_result'] else 'rejected'

graph = StateGraph(ToolSpecState)
graph.add_node('validate', validate_spec)
graph.add_node('qc', check_quality)
graph.set_entry_point('validate')
graph.add_edge('validate', 'qc')
graph.add_edge('qc', END)
graph = graph.compile()