from typing import TypedDict
from langgraph.graph import StateGraph, END

class EduState(TypedDict):
    material_id: str
    safety_verified: bool
    age_appropriateness_checked: bool

def validate_safety(state: EduState):
    print(f"Validating safety for {state['material_id']}")
    return {"safety_verified": True}

def validate_pedagogy(state: EduState):
    print(f"Checking pedagogical alignment for {state['material_id']}")
    return {"age_appropriateness_checked": True}

workflow = StateGraph(EduState)
workflow.add_node("safety_check", validate_safety)
workflow.add_node("pedagogy_check", validate_pedagogy)
workflow.set_entry_point("safety_check")
workflow.add_edge("safety_check", "pedagogy_check")
workflow.add_edge("pedagogy_check", END)

graph = workflow.compile()
