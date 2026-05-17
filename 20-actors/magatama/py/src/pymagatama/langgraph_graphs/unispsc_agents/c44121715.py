from typing import TypedDict
from langgraph.graph import StateGraph, END

class StationeryState(TypedDict):
    item_name: str
    specs: dict
    is_compliant: bool

def validate_specs(state: StationeryState):
    required = ['Tip diameter', 'Ink color']
    state['is_compliant'] = all(k in state['specs'] for k in required)
    return state

def finalize_procurement(state: StationeryState):
    print(f"Processing procurement for {state['item_name']}: Compliant={state['is_compliant']}")
    return state

graph = StateGraph(StationeryState)
graph.add_node("validate", validate_specs)
graph.add_node("finalize", finalize_procurement)
graph.set_entry_point("validate")
graph.add_edge("validate", "finalize")
graph.add_edge("finalize", END)
graph = graph.compile()