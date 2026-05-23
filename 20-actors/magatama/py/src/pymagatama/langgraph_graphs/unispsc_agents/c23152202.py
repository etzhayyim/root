from typing import TypedDict
from langgraph.graph import StateGraph, END

class WeldingGraphState(TypedDict):
    spec_data: dict
    validation_passed: bool
    robot_compatibility: bool

def validate_specs(state: WeldingGraphState):
    # logic for technical spec validation
    state['validation_passed'] = all(k in state['spec_data'] for k in ['amps', 'duty_cycle'])
    return state

def check_robot_compatibility(state: WeldingGraphState):
    # logic for checking robotic interface protocols
    state['robot_compatibility'] = state.get('spec_data', {}).get('protocol') == 'EtherCAT'
    return state

graph = StateGraph(WeldingGraphState)
graph.add_node('validate', validate_specs)
graph.add_node('check_robot', check_robot_compatibility)
graph.add_edge('validate', 'check_robot')
graph.add_edge('check_robot', END)
graph.set_entry_point('validate')
graph = graph.compile()
