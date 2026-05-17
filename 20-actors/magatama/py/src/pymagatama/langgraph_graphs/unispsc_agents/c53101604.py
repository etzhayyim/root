from typing import TypedDict
from langgraph.graph import StateGraph, END

class ApparelState(TypedDict):
    spec_data: dict
    approved: bool

def validate_materials(state: ApparelState):
    composition = state['spec_data'].get('fabric_composition', '')
    return {'approved': 'synthetic' in composition or 'cotton' in composition}

def quality_check(state: ApparelState):
    return {'approved': state['spec_data'].get('color_fastness_rating', 0) >= 4}

workflow = StateGraph(ApparelState)
workflow.add_node('material_val', validate_materials)
workflow.add_node('quality_val', quality_check)
workflow.set_entry_point('material_val')
workflow.add_edge('material_val', 'quality_val')
workflow.add_edge('quality_val', END)
graph = workflow.compile()