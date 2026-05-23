from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RagProcurementState(TypedDict):
    material: str
    absorbency: float
    inspection_passed: bool

def validate_material(state: RagProcurementState):
    state['inspection_passed'] = state['material'] in ['cotton', 'microfiber']
    return state

workflow = StateGraph(RagProcurementState)
workflow.add_node('validation', validate_material)
workflow.set_entry_point('validation')
workflow.add_edge('validation', END)
graph = workflow.compile()
