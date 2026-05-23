from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SterilizationCartState(TypedDict):
    item_id: str
    material_spec: str
    compliance_docs: List[str]
    validation_status: bool

def validate_materials(state: SterilizationCartState):
    # Industry standard check for medical-grade materials
    valid = state['material_spec'] in ['Stainless Steel 304', 'Medical Grade Plastic']
    return {'validation_status': valid}

def check_compliance(state: SterilizationCartState):
    # Verify ISO 13485 documentation
    compliance = 'ISO_13485' in state['compliance_docs']
    return {'validation_status': state['validation_status'] and compliance}

graph = StateGraph(SterilizationCartState)
graph.add_node('validate_mat', validate_materials)
graph.add_node('check_comp', check_compliance)
graph.add_edge('validate_mat', 'check_comp')
graph.add_edge('check_comp', END)
graph.set_entry_point('validate_mat')
graph = graph.compile()
