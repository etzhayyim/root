from typing import TypedDict
from langgraph.graph import StateGraph, END
class RobotState(TypedDict):
    spec_data: dict
    validation_status: str
    risk_score: float
def validate_robot_specs(state: RobotState):
    specs = state['spec_data']
    if 'payload_capacity_kg' in specs and specs['payload_capacity_kg'] > 0:
        return {'validation_status': 'passed', 'risk_score': 0.2}
    return {'validation_status': 'failed', 'risk_score': 0.9}
def compute_risk(state: RobotState):
    return {'risk_score': state['risk_score'] * 1.5}
graph = StateGraph(RobotState)
graph.add_node('validate', validate_robot_specs)
graph.add_node('risk_calc', compute_risk)
graph.add_edge('validate', 'risk_calc')
graph.add_edge('risk_calc', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()
