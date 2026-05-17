from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RotorState(TypedDict):
    part_id: str
    material_certified: bool
    torque_check_passed: bool
    qa_status: str

def validate_material(state: RotorState):
    return {"material_certified": True if state.get"part_id".startswith("A") else False}

def perform_torque_test(state: RotorState):
    # Simulate mechanical check
    return {"torque_check_passed": True}

def finalize_qa(state: RotorState):
    state["qa_status"] = "APPROVED" if state["material_certified"] and state["torque_check_passed"] else "REJECTED"
    return state

graph = StateGraph(RotorState)
graph.add_node("validate", validate_material)
graph.add_node("torque", perform_torque_test)
graph.add_node("qa", finalize_qa)
graph.set_entry_point("validate")
graph.add_edge("validate", "torque")
graph.add_edge("torque", "qa")
graph.add_edge("qa", END)
graph = graph.compile()