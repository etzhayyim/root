from typing import TypedDict
from langgraph.graph import StateGraph, END

class CanoeProcurementState(TypedDict):
    model_name: str
    material: str
    safety_check_passed: bool
    finalized: bool

def validate_materials(state: CanoeProcurementState):
    print(f"Validating material: {state['material']}")
    return {'safety_check_passed': True}

def finalize_order(state: CanoeProcurementState):
    print("Finalizing procurement order for kayak/canoe.")
    return {'finalized': True}

graph = StateGraph(CanoeProcurementState)
graph.add_node("validate", validate_materials)
graph.add_node("finalize", finalize_order)
graph.set_entry_point("validate")
graph.add_edge("validate", "finalize")
graph.add_edge("finalize", END)
graph = graph.compile()
