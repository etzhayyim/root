from typing import TypedDict
from langgraph.graph import StateGraph, END

class CraftState(TypedDict):
    material_type: str
    thickness: float
    is_compliant: bool

def validate_material(state: CraftState):
    state['is_compliant'] = state['material_type'] == 'cork' and state['thickness'] > 0
    return state

workflow = StateGraph(CraftState)
workflow.add_node('validate', validate_material)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
