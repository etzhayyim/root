from typing import TypedDict
from langgraph.graph import StateGraph, END

class RobotState(TypedDict):
    specs: dict
    validation_status: str

def validate_robot_specs(state: RobotState):
    required = ['payload', 'reach']
    valid = all(k in state['specs'] for k in required)
    return {'validation_status': 'passed' if valid else 'rejected'}

def route_verification(state: RobotState):
    return 'end' if state['validation_status'] == 'passed' else 'end'

graph = StateGraph(RobotState)
graph.add_node('validate', validate_robot_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()
