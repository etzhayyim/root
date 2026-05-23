from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class PipeSpecState(TypedDict):
    spec_data: dict
    validation_passed: bool
    errors: List[str]

def validate_materials(state: PipeSpecState):
    m_grade = state['spec_data'].get('material')
    if not m_grade: state['errors'].append('Missing material grade'); state['validation_passed'] = False
    return state

def check_dimensions(state: PipeSpecState):
    if 'schedule' not in state['spec_data']: state['errors'].append('Missing schedule'); state['validation_passed'] = False
    return state

graph = StateGraph(PipeSpecState)
graph.add_node('material_check', validate_materials)
graph.add_node('dimension_check', check_dimensions)
graph.set_entry_point('material_check')
graph.add_edge('material_check', 'dimension_check')
graph.add_edge('dimension_check', END)
graph = graph.compile()
