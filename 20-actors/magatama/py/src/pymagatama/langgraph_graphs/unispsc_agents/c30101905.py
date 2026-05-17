from typing import TypedDict
from langgraph.graph import StateGraph, END

class CoilState(TypedDict):
    material_grade: str
    thickness: float
    inspection_passed: bool

def validate_grade(state: CoilState) -> CoilState:
    if state['material_grade'] not in ['SUS304', 'SUS316']:
        raise ValueError('Unsupported stainless grade')
    return state

def check_dimensions(state: CoilState) -> CoilState:
    state['inspection_passed'] = state['thickness'] > 0
    return state

graph = StateGraph(CoilState)
graph.add_node('validate', validate_grade)
graph.add_node('inspection', check_dimensions)
graph.add_edge('validate', 'inspection')
graph.add_edge('inspection', END)
graph.set_entry_point('validate')
graph = graph.compile()