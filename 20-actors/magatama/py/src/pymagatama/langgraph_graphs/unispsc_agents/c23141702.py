from typing import TypedDict
from langgraph.graph import StateGraph, END

class RobotState(TypedDict):
    spec_data: dict
    validation_status: bool

def validate_robot_specs(state: RobotState):
    required = ['payload', 'reach', 'certification']
    state['validation_status'] = all(k in state['spec_data'] for k in required)
    return state

graph = StateGraph(RobotState)
graph.add_node('validate', validate_robot_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
