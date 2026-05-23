from typing import TypedDict
from langgraph.graph import StateGraph, END

class AssemblyState(TypedDict):
    specs: dict
    validated: bool
    error: str

def validate_materials(state: AssemblyState):
    grade = state['specs'].get('material_grade')
    state['validated'] = grade in ['304', '316', '316L']
    return state

def check_dimensions(state: AssemblyState):
    if state['validated']:
        tolerance = state['specs'].get('tolerance', 0.0)
        state['validated'] = tolerance <= 0.05
    return state

builder = StateGraph(AssemblyState)
builder.add_node('validate_materials', validate_materials)
builder.add_node('check_dimensions', check_dimensions)
builder.set_entry_point('validate_materials')
builder.add_edge('validate_materials', 'check_dimensions')
builder.add_edge('check_dimensions', END)
graph = builder.compile()
