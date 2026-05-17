from typing import TypedDict
from langgraph.graph import StateGraph, END

class DentalTrayState(TypedDict):
    material: str
    is_autoclavable: bool
    validation_passed: bool

def validate_material(state: DentalTrayState):
    # Business logic for dental grade materials
    valid_materials = ['304_stainless', 'polypropylene', 'medical_grade_plastic']
    return {'validation_passed': state['material'] in valid_materials}

def check_autoclave_req(state: DentalTrayState):
    # Ensure dental sterilization compliance
    return {'validation_passed': state['validation_passed'] and state['is_autoclavable']}

graph = StateGraph(DentalTrayState)
graph.add_node('validate_material', validate_material)
graph.add_node('check_autoclave', check_autoclave_req)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'check_autoclave')
graph.add_edge('check_autoclave', END)
compile_graph = graph.compile()