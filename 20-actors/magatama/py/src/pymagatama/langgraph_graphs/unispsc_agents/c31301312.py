from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ForgingState(TypedDict):
    material_spec: str
    tolerance: float
    inspection_passed: bool
    logs: List[str]

def validate_material(state: ForgingState):
    state['logs'].append('Validating bronze grade specs...')
    state['inspection_passed'] = 'Bronze' in state['material_spec']
    return state

def check_tolerance(state: ForgingState):
    if state['tolerance'] < 0.05:
        state['logs'].append('Tolerance within precision limits.')
    else:
        state['inspection_passed'] = False
        state['logs'].append('Tolerance exceeds limits.')
    return state

graph = StateGraph(ForgingState)
graph.add_node('validate_material', validate_material)
graph.add_node('check_tolerance', check_tolerance)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'check_tolerance')
graph.add_edge('check_tolerance', END)
graph = graph.compile()