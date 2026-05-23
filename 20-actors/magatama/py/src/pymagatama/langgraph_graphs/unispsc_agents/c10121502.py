from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MiningState(TypedDict):
    props_id: str
    load_bearing_capacity: float
    inspection_result: bool
    is_safe: bool

def validate_load(state: MiningState) -> MiningState:
    # Logic to ensure the prop meets minimum load-bearing requirements for safety
    state['is_safe'] = state['load_bearing_capacity'] >= 50.0
    return state

def approve_prop(state: MiningState) -> MiningState:
    state['inspection_result'] = True
    return state

graph = StateGraph(MiningState)
graph.add_node('validate_load', validate_load)
graph.add_node('approve_prop', approve_prop)
graph.set_entry_point('validate_load')
graph.add_edge('validate_load', 'approve_prop')
graph.add_edge('approve_prop', END)

graph = graph.compile()
