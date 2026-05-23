from typing import TypedDict
from langgraph.graph import StateGraph, END

class BearingState(TypedDict):
    specs: dict
    validated: bool
    error: str

def validate_tolerance(state: BearingState):
    tolerance = state['specs'].get('tolerance', 0.0)
    if tolerance < 0.01: state['validated'] = True
    else: state['validated'] = False
    return state

def check_material(state: BearingState):
    if 'material' in state['specs']: state['validated'] = True
    else: state['validated'] = False
    return state

graph = StateGraph(BearingState)
graph.add_node('tolerance_check', validate_tolerance)
graph.add_node('material_check', check_material)
graph.add_edge('tolerance_check', 'material_check')
graph.add_edge('material_check', END)
graph.set_entry_point('tolerance_check')
graph = graph.compile()
