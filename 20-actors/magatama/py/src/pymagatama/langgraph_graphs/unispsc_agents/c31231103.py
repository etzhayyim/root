from typing import TypedDict
from langgraph.graph import StateGraph, END

class BrassStockState(TypedDict):
    alloy_grade: str
    dimensions: dict
    compliance_verified: bool

def validate_material_grade(state: BrassStockState):
    valid_grades = ['C360', 'C385', 'C464']
    state['compliance_verified'] = state['alloy_grade'] in valid_grades
    return state

def check_dimensions(state: BrassStockState):
    if state['dimensions'].get('diameter', 0) <= 0:
        state['compliance_verified'] = False
    return state

graph = StateGraph(BrassStockState)
graph.add_node('validate_grade', validate_material_grade)
graph.add_node('check_dims', check_dimensions)
graph.set_entry_point('validate_grade')
graph.add_edge('validate_grade', 'check_dims')
graph.add_edge('check_dims', END)
graph = graph.compile()