from typing import TypedDict
from langgraph.graph import StateGraph, END

class RiserSpecState(TypedDict):
    material: str
    weight_limit: float
    height_mm: int
    is_valid: bool

def validate_specs(state: RiserSpecState):
    state['is_valid'] = state['weight_limit'] > 0 and state['height_mm'] > 0
    return {'is_valid': state['is_valid']}

def process_procurement(state: RiserSpecState):
    print(f"Processing procurement for risers: {state}")
    return {"status": "verified"}

graph = StateGraph(RiserSpecState)
graph.add_node("validate", validate_specs)
graph.add_node("process", process_procurement)
graph.set_entry_point("validate")
graph.add_edge("validate", "process")
graph.add_edge("process", END)
graph = graph.compile()