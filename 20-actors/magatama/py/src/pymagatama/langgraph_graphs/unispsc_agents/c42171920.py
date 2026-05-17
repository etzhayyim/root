from langgraph.graph import StateGraph, END
from typing import TypedDict, List
class EMSClothingState(TypedDict):
    material_specs: dict
    compliance_docs: List[str]
    approved: bool
def validate_materials(state: EMSClothingState):
    state['approved'] = 'iso_certified' in state['material_specs']
    return state
def check_compliance(state: EMSClothingState):
    if not state.get('compliance_docs'):
        state['approved'] = False
    return state
graph = StateGraph(EMSClothingState)
graph.add_node('material_validation', validate_materials)
graph.add_node('compliance_check', check_compliance)
graph.set_entry_point('material_validation')
graph.add_edge('material_validation', 'compliance_check')
graph.add_edge('compliance_check', END)
graph = graph.compile()