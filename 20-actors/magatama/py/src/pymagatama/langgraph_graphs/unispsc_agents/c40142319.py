from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PipeState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_material(state: PipeState):
    material = state.get('specs', {}).get('material')
    if not material:
        state['validation_errors'].append('Missing material specification')
    return state

def check_pressure_rating(state: PipeState):
    rating = state.get('specs', {}).get('pressure_rating')
    if not rating or float(rating) <= 0:
        state['validation_errors'].append('Invalid pressure rating')
    return state

def finalize_check(state: PipeState):
    state['is_compliant'] = len(state['validation_errors']) == 0
    return state

graph = StateGraph(PipeState)
graph.add_node('val_mat', validate_material)
graph.add_node('val_press', check_pressure_rating)
graph.add_node('final', finalize_check)
graph.set_entry_point('val_mat')
graph.add_edge('val_mat', 'val_press')
graph.add_edge('val_press', 'final')
graph.add_edge('final', END)
graph.compile()
