from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SailBoomState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_material(state: SailBoomState):
    material = state['specs'].get('material', '')
    if material not in ['Carbon Fiber', 'Aluminum 6061-T6', 'Stainless Steel']:
        state['validation_errors'].append('Invalid material specification.')
    return state

def check_dimensions(state: SailBoomState):
    if state['specs'].get('length', 0) <= 0:
        state['validation_errors'].append('Invalid length specified.')
    return state

def finalize_check(state: SailBoomState):
    state['is_compliant'] = len(state['validation_errors']) == 0
    return state

graph = StateGraph(SailBoomState)
graph.add_node('validate_material', validate_material)
graph.add_node('check_dimensions', check_dimensions)
graph.add_node('finalize', finalize_check)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'check_dimensions')
graph.add_edge('check_dimensions', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
