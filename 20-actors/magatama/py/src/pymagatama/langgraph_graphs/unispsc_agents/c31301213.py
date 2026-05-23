from typing import TypedDict
from langgraph.graph import StateGraph, END

class ForgingState(TypedDict):
    part_id: str
    material_spec: str
    tolerance_check: bool
    approved: bool

def validate_material(state: ForgingState):
    # Business logic for zinc alloy validation
    is_valid = "Zinc" in state.get('material_spec', '')
    return {"material_spec": state['material_spec'], "tolerance_check": is_valid}

def final_qc_check(state: ForgingState):
    return {"approved": state['tolerance_check']}

graph = StateGraph(ForgingState)
graph.add_node("validate", validate_material)
graph.add_node("qc", final_qc_check)
graph.add_edge("validate", "qc")
graph.add_edge("qc", END)
graph.set_entry_point("validate")
graph = graph.compile()
