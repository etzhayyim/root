from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    part_number: str
    material_certified: bool
    inspection_passed: bool

def validate_materials(state: ProcurementState):
    # Simulate alloy verification logic for Waspaloy
    state['material_certified'] = True
    return 'check_inspection'

def run_inspection(state: ProcurementState):
    # Simulate NDT/Dimension validation
    state['inspection_passed'] = True
    return 'complete'

graph = StateGraph(ProcurementState)
graph.add_node('validate_materials', validate_materials)
graph.add_node('check_inspection', run_inspection)
graph.set_entry_point('validate_materials')
graph.add_edge('validate_materials', 'check_inspection')
graph.add_edge('check_inspection', END)
graph = graph.compile()