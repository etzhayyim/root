from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class GaitBeltState(TypedDict):
    material_tensile_strength: float
    has_safety_cert: bool
    is_approved: bool

def validate_durability(state: GaitBeltState):
    state['is_approved'] = state['material_tensile_strength'] > 1500 and state['has_safety_cert']
    return state

workflow = StateGraph(GaitBeltState)
workflow.add_node('validate_durability', validate_durability)
workflow.set_entry_point('validate_durability')
workflow.add_edge('validate_durability', END)
graph = workflow.compile()
