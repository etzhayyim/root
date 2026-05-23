from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class HaspState(TypedDict):
    material: str
    pull_strength_n: float
    test_passed: bool

def validate_hasp_spec(state: HaspState):
    # Business logic for industrial hasp compliance
    is_compliant = state['pull_strength_n'] > 500 and state['material'] in ['stainless_steel', 'hardened_steel']
    return {"test_passed": is_compliant}

def route_by_compliance(state: HaspState):
    return "approved" if state['test_passed'] else END

workflow = StateGraph(HaspState)
workflow.add_node("validate", validate_hasp_spec)
workflow.set_entry_point("validate")
workflow.add_edge("validate", END)

graph = workflow.compile()
