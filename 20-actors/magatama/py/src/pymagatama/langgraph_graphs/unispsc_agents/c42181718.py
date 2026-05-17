from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class EKGState(TypedDict):
    part_number: str
    compatibility_list: List[str]
    validation_status: bool

def validate_specs(state: EKGState):
    # Simulate CAD/Spec validation logic for medical recording pens
    if state['part_number'] and len(state['compatibility_list']) > 0:
        return {"validation_status": True}
    return {"validation_status": False}

graph = StateGraph(EKGState)
graph.add_node("validate", validate_specs)
graph.set_entry_point("validate")
graph.add_edge("validate", END)
graph = graph.compile()