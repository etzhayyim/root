from typing import TypedDict
from langgraph.graph import StateGraph, END

class RubberSpecState(TypedDict):
    material_grade: str
    hardness_shore_a: float
    dimensions_mm: dict
    validation_passed: bool

def validate_specs(state: RubberSpecState):
    # Basic logic: ensure hardness is within industrial range
    passed = 30 <= state['hardness_shore_a'] <= 90
    return {'validation_passed': passed}

def approval_check(state: RubberSpecState):
    return 'approved' if state['validation_passed'] else 'rejected'

workflow = StateGraph(RubberSpecState)
workflow.add_node('validator', validate_specs)
workflow.set_entry_point('validator')
workflow.add_edge('validator', END)
graph = workflow.compile()