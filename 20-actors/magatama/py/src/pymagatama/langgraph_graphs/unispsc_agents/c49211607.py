from typing import TypedDict
from langgraph.graph import StateGraph, END

class DivotRepairState(TypedDict):
    specs: dict
    approved: bool

def validate_materials(state: DivotRepairState):
    material = state['specs'].get('material', '')
    return {'approved': material in ['Stainless Steel', 'Aluminum Alloy']}

workflow = StateGraph(DivotRepairState)
workflow.add_node('validation', validate_materials)
workflow.set_entry_point('validation')
workflow.add_edge('validation', END)
graph = workflow.compile()
