from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ScreenDoorState(TypedDict):
    specs: dict
    validation_passed: bool
    error_logs: List[str]

def validate_specs(state: ScreenDoorState):
    required = ['dimensions_h_w', 'frame_finish_specification']
    passed = all(k in state['specs'] for k in required)
    return {'validation_passed': passed, 'error_logs': [] if passed else ['Missing mandatory specifications']}

def check_durability(state: ScreenDoorState):
    # Simulate CAD/Spec validation for material strength
    if state.get('validation_passed'):
        return {'error_logs': state['error_logs'] + ['Durability check for hinges and mesh confirmed']}
    return state

graph = StateGraph(ScreenDoorState)
graph.add_node('validate', validate_specs)
graph.add_node('durability', check_durability)
graph.add_edge('validate', 'durability')
graph.add_edge('durability', END)
graph.set_entry_point('validate')
graph = graph.compile()
