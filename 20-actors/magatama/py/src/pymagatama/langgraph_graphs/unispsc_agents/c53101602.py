from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ShirtProcurementState(TypedDict):
    material_info: str
    quality_check_passed: bool
    compliance_tags: List[str]

def validate_material(state: ShirtProcurementState):
    # Simulate material validation logic
    state['quality_check_passed'] = 'cotton' in state['material_info'].lower()
    return state

def check_compliance(state: ShirtProcurementState):
    state['compliance_tags'] = ['Oeko-Tex'] if state['quality_check_passed'] else []
    return state

graph = StateGraph(ShirtProcurementState)
graph.add_node('validate_material', validate_material)
graph.add_node('check_compliance', check_compliance)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'check_compliance')
graph.add_edge('check_compliance', END)
graph = graph.compile()
