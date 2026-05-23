from typing import TypedDict
from langgraph.graph import StateGraph, END

class FrozenProductState(TypedDict):
    temperature_log: list
    is_compliant: bool

def validate_cold_chain(state: FrozenProductState):
    state['is_compliant'] = all(t < -18 for t in state['temperature_log'])
    return state

def route_logic(state: FrozenProductState):
    return 'compliant' if state['is_compliant'] else 'reject'

graph = StateGraph(FrozenProductState)
graph.add_node('validate', validate_cold_chain)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
