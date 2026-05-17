from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class GratingState(TypedDict):
    specs: dict
    validation_checks: List[str]
    approved: bool

def validate_load_capacity(state: GratingState):
    load = state['specs'].get('load_capacity', 0)
    state['validation_checks'].append(f'Load capacity {load}kN checked')
    return state

def check_material_grade(state: GratingState):
    grade = state['specs'].get('material', '')
    state['approved'] = grade in ['SUS304', 'SUS316']
    return state

graph = StateGraph(GratingState)
graph.add_node('validate_load', validate_load_capacity)
graph.add_node('check_material', check_material_grade)
graph.add_edge('validate_load', 'check_material')
graph.add_edge('check_material', END)
graph.set_entry_point('validate_load')
graph = graph.compile()