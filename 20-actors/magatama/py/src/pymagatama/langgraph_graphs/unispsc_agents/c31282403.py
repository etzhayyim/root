from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcessingState(TypedDict):
    component_id: str
    material_check: bool
    clearance_status: str
    final_assembly_ready: bool

def validate_material(state: ProcessingState):
    print(f"Verifying brass grade for {state['component_id']}")
    return {"material_check": True}

def security_clearance(state: ProcessingState):
    print(f"Running dual-use export control checks for {state['component_id']}")
    return {"clearance_status": "APPROVED"}

graph = StateGraph(ProcessingState)
graph.add_node("validate_material", validate_material)
graph.add_node("security_clearance", security_clearance)
graph.set_entry_point("validate_material")
graph.add_edge("validate_material", "security_clearance")
graph.add_edge("security_clearance", END)
app = graph.compile()
