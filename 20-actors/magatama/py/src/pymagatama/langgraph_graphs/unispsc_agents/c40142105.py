from typing import TypedDict
from langgraph.graph import StateGraph, END

class PipeSpecState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_material(state: PipeSpecState):
    grade = state['spec_data'].get('material_grade')
    state['is_compliant'] = grade is not None and len(grade) > 0
    return state

def check_dimensions(state: PipeSpecState):
    if state['is_compliant']:
        od = state['spec_data'].get('outer_diameter', 0)
        state['is_compliant'] = od > 0
    return state

graph = StateGraph(PipeSpecState)
graph.add_node('validate', validate_material)
graph.add_node('dimensions', check_dimensions)
graph.add_edge('validate', 'dimensions')
graph.add_edge('dimensions', END)
graph.set_entry_point('validate')
graph = graph.compile()