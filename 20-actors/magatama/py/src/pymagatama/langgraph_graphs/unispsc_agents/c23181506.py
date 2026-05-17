from typing import TypedDict
from langgraph.graph import StateGraph, END

class RobotState(TypedDict):
    spec_data: dict
    validation_score: float
    approved: bool

def validate_robot_specs(state: RobotState):
    specs = state['spec_data']
    score = 1.0 if 'Payload Capacity' in specs and 'Reach Radius' in specs else 0.0
    return {'validation_score': score, 'approved': score > 0.5}

graph = StateGraph(RobotState)
graph.add_node('validate', validate_robot_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()