from langgraph.graph import StateGraph, END
from typing import TypedDict

class ShotputState(TypedDict):
    weight: float
    diameter: float
    certification_valid: bool
    approved: bool

def validate_specs(state: ShotputState):
    # Industry standard: 7.26kg for men, 4kg for women
    if state['weight'] in [7.26, 4.0] and state['certification_valid']:
        return {'approved': True}
    return {'approved': False}

def process_procurement(state: ShotputState):
    print(f"Processing procurement for shotput: {state['approved']}")
    return state

graph = StateGraph(ShotputState)
graph.add_node("validate", validate_specs)
graph.add_node("process", process_procurement)
graph.set_entry_point("validate")
graph.add_edge("validate", "process")
graph.add_edge("process", END)
graph = graph.compile()