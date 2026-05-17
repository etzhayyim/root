from typing import TypedDict
from langgraph.graph import StateGraph, END

class AssemblyState(TypedDict):
    part_id: str
    weld_integrity_score: float
    uv_reflectivity: float
    verified: bool

def validate_weld(state: AssemblyState):
    state['verified'] = state['weld_integrity_score'] > 0.95
    return state

def check_uv_spec(state: AssemblyState):
    if state['uv_reflectivity'] < 0.90:
        raise ValueError('Insufficient UV reflectivity')
    return state

graph = StateGraph(AssemblyState)
graph.add_node('validate_weld', validate_weld)
graph.add_node('check_uv_spec', check_uv_spec)
graph.set_entry_point('validate_weld')
graph.add_edge('validate_weld', 'check_uv_spec')
graph.add_edge('check_uv_spec', END)
graph = graph.compile()