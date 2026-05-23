from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class WallMaterialState(TypedDict):
    material_type: str
    spec_requirements: List[str]
    approved: bool

def validate_materials(state: WallMaterialState):
    # Check VOC compliance logic
    state['approved'] = 'Low VOC' in state['spec_requirements']
    return 'APPROVED' if state['approved'] else 'REJECTED'

workflow = StateGraph(WallMaterialState)
workflow.add_node('validation', validate_materials)
workflow.set_entry_point('validation')
workflow.add_edge('validation', END)
graph = workflow.compile()
