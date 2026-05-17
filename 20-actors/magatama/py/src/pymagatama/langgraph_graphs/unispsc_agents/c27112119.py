from typing import TypedDict
from langgraph.graph import StateGraph, END

class State(TypedDict):
    reach_length_cm: float
    bulb_type: str
    is_verified: bool

def validate_tool_specs(state: State):
    state['is_verified'] = state['reach_length_cm'] > 0 and state['bulb_type'] != "- unknown -"
    return state

graph = StateGraph(State)
graph.add_node("validate", validate_tool_specs)
graph.set_entry_point("validate")
graph.add_edge("validate", END)
graph = graph.compile()