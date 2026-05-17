from typing import TypedDict
from langgraph.graph import StateGraph, END

class FreezerState(TypedDict):
    temp_celsius: float
    capacity_liters: float
    is_validated: bool

def validate_specs(state: FreezerState):
    state['is_validated'] = state['temp_celsius'] <= -20.0 and state['capacity_liters'] > 0
    return state

def safety_check(state: FreezerState):
    return {'is_validated': state['is_validated']}

graph = StateGraph(FreezerState)
graph.add_node("validate", validate_specs)
graph.add_node("safety", safety_check)
graph.add_edge("validate", "safety")
graph.add_edge("safety", END)
graph.set_entry_point("validate")
compiled_graph = graph.compile()