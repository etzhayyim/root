from typing import TypedDict
from langgraph.graph import StateGraph, END

class DieCastState(TypedDict):
    spec_data: dict
    approved: bool
    error: str

def validate_material(state: DieCastState):
    grade = state['spec_data'].get('grade')
    state['approved'] = grade in ['SUS304', 'SUS316']
    if not state['approved']: state['error'] = 'Invalid material grade'
    return state

def check_dimensions(state: DieCastState):
    if state['approved']:
        state['approved'] = state['spec_data'].get('tolerance', 0.05) <= 0.1
    return state

graph = StateGraph(DieCastState)
graph.add_node('material_check', validate_material)
graph.add_node('dimension_check', check_dimensions)
graph.add_edge('material_check', 'dimension_check')
graph.add_edge('dimension_check', END)
graph.set_entry_point('material_check')
graph = graph.compile()
