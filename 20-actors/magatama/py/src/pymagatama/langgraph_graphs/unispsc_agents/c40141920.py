from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class DuctProcurementState(TypedDict):
    material_grade: str
    thickness: float
    specs_verified: bool

def validate_material(state: DuctProcurementState):
    valid_grades = ['SUS304', 'SUS316']
    state['specs_verified'] = state['material_grade'] in valid_grades
    return state

def check_thickness(state: DuctProcurementState):
    if state['thickness'] < 0.5:
        state['specs_verified'] = False
    return state

graph = StateGraph(DuctProcurementState)
graph.add_node('validate', validate_material)
graph.add_node('thickness_check', check_thickness)
graph.add_edge('validate', 'thickness_check')
graph.add_edge('thickness_check', END)
graph.set_entry_point('validate')
graph = graph.compile()