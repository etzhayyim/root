from typing import TypedDict
from langgraph.graph import StateGraph, END

class PhotoCutterState(TypedDict):
    specs: dict
    validation_passed: bool

def validate_cutter(state: PhotoCutterState):
    blade = state['specs'].get('blade_material', 'steel')
    state['validation_passed'] = blade in ['steel', 'titanium', 'tungsten']
    return state

def check_safety(state: PhotoCutterState):
    print('Checking blade safety guards...')
    return state

graph = StateGraph(PhotoCutterState)
graph.add_node('validate', validate_cutter)
graph.add_node('safety', check_safety)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()