from typing import TypedDict
from langgraph.graph import StateGraph, END

class PruneState(TypedDict):
    batch_id: str
    moisture_content: float
    inspection_passed: bool

def validate_moisture(state: PruneState):
    return {"inspection_passed": 15.0 <= state['moisture_content'] <= 25.0}

def route_by_quality(state: PruneState):
    return "approved" if state['inspection_passed'] else "rejected"

graph = StateGraph(PruneState)
graph.add_node("validate", validate_moisture)
graph.add_edge("validate", END)
graph.set_entry_point("validate")
graph = graph.compile()
