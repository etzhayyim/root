from typing import TypedDict
from langgraph.graph import StateGraph, END

class ToyPailState(TypedDict):
    material_safety: bool
    impact_test_passed: bool
    approved: bool

def validate_safety(state: ToyPailState) -> ToyPailState:
    state['approved'] = state['material_safety'] and state['impact_test_passed']
    return state

workflow = StateGraph(ToyPailState)
workflow.add_node('safety_check', validate_safety)
workflow.set_entry_point('safety_check')
workflow.add_edge('safety_check', END)
graph = workflow.compile()