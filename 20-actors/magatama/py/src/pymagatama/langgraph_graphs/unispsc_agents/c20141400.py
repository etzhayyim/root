from typing import TypedDict
from langgraph.graph import StateGraph, END

class BearingState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_approved: bool

def validate_material(state: BearingState):
    material = state['spec_data'].get('material')
    if not material: state['validation_errors'].append('Missing Material')
    return state

def check_tolerances(state: BearingState):
    tolerance = state['spec_data'].get('tolerance')
    if tolerance and tolerance > 0.05: state['validation_errors'].append('Tolerance High')
    return state

graph = StateGraph(BearingState)
graph.add_node('validate_material', validate_material)
graph.add_node('check_tolerances', check_tolerances)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'check_tolerances')
graph.add_edge('check_tolerances', END)
compiled_graph = graph.compile()