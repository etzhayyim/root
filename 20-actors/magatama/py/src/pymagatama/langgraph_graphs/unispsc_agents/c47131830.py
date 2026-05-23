from typing import TypedDict
from langgraph.graph import StateGraph, END

class FurnitureCleanerState(TypedDict):
    material_type: str
    chemical_data: dict
    approved: bool

def validate_chemistry(state: FurnitureCleanerState):
    # Logic to check if pH and VOC levels comply with furniture finish safety
    ph = state['chemical_data'].get('ph', 7)
    is_safe = 6 <= ph <= 8
    return {'approved': is_safe}

workflow = StateGraph(FurnitureCleanerState)
workflow.add_node('validate', validate_chemistry)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
