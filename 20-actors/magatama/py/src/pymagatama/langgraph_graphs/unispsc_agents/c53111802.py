from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ShoeState(TypedDict):
    specs: dict
    validation_errors: List[str]
    approved: bool

def validate_material(state: ShoeState):
    material = state['specs'].get('material', '')
    if not material: state['validation_errors'].append('Missing material info')
    return state

def validate_safety(state: ShoeState):
    if state['specs'].get('slip_resistance') == 'low': state['validation_errors'].append('Hazardous sole')
    return state

def final_check(state: ShoeState):
    state['approved'] = len(state['validation_errors']) == 0
    return state

graph = StateGraph(ShoeState)
graph.add_node('material_check', validate_material)
graph.add_node('safety_check', validate_safety)
graph.add_node('final_approval', final_check)
graph.set_entry_point('material_check')
graph.add_edge('material_check', 'safety_check')
graph.add_edge('safety_check', 'final_approval')
graph.add_edge('final_approval', END)
graph = graph.compile()