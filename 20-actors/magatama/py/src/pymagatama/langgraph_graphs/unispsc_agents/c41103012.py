from typing import TypedDict
from langgraph.graph import StateGraph, END

class RefrigeratorState(TypedDict):
    temp_range: float
    is_explosion_proof: bool
    is_compliant: bool

def validate_safety_specs(state: RefrigeratorState) -> RefrigeratorState:
    state['is_compliant'] = state['is_explosion_proof'] and state['temp_range'] <= 4.0
    return state

graph = StateGraph(RefrigeratorState)
graph.add_node('safety_check', validate_safety_specs)
graph.set_entry_point('safety_check')
graph.add_edge('safety_check', END)
graph = graph.compile()