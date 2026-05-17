from typing import TypedDict
from langgraph.graph import StateGraph, END

class ToyState(TypedDict):
    product_name: str
    material_safety_passed: bool
    velocity_test_passed: bool
    compliant: bool

def validate_safety(state: ToyState):
    state['compliant'] = state['material_safety_passed'] and state['velocity_test_passed']
    return state

workflow = StateGraph(ToyState)
workflow.add_node('safety_check', validate_safety)
workflow.set_entry_point('safety_check')
workflow.add_edge('safety_check', END)
graph = workflow.compile()