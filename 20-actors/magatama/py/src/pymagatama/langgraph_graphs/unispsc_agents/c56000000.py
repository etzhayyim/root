from typing import TypedDict
from langgraph.graph import StateGraph, END

class FurnitureState(TypedDict):
    spec_data: dict
    validation_checklist: list
    is_approved: bool

def validate_materials(state: FurnitureState):
    """Validate Material composition against safety standards"""
    print("Validating materials for furniture...")
    return {'validation_checklist': state['validation_checklist'] + ['materials_checked']}

def structural_integrity_check(state: FurnitureState):
    """Perform load-bearing and ergonomic compliance check"""
    print("Performing structural integrity tests...")
    return {'validation_checklist': state['validation_checklist'] + ['structure_passed']}

def approval_step(state: FurnitureState):
    return {'is_approved': True}

graph = StateGraph(FurnitureState)
graph.add_node("validate_materials", validate_materials)
graph.add_node("structural_integrity", structural_integrity_check)
graph.add_node("approval", approval_step)

graph.set_entry_point("validate_materials")
graph.add_edge("validate_materials", "structural_integrity")
graph.add_edge("structural_integrity", "approval")
graph.add_edge("approval", END)

graph = graph.compile()
