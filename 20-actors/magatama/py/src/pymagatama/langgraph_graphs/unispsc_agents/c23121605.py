from typing import TypedDict
from langgraph.graph import StateGraph, END

class RobotControlState(TypedDict):
    spec_data: dict
    validation_passed: bool
    error_log: list

def validate_specs(state: RobotControlState):
    required = ['voltage', 'protocol', 'safety_level']
    passed = all(k in state['spec_data'] for k in required)
    return {'validation_passed': passed}

def process_deployment(state: RobotControlState):
    return {'error_log': ['Safety audit initiated'] if state['validation_passed'] else ['Missing specs']}

graph = StateGraph(RobotControlState)
graph.add_node('validate', validate_specs)
graph.add_node('deploy', process_deployment)
graph.set_entry_point('validate')
graph.add_edge('validate', 'deploy')
graph.add_edge('deploy', END)
graph = graph.compile()