from typing import TypedDict
from langgraph.graph import StateGraph, END

class RobotProcurementState(TypedDict):
    payload: float
    safety_certs: list
    is_compliant: bool

def validate_specs(state: RobotProcurementState):
    if state['payload'] > 0 and len(state['safety_certs']) > 0:
        return {'is_compliant': True}
    return {'is_compliant': False}

def deploy_robot(state: RobotProcurementState):
    print('Robot procurement process verified and optimized.')

graph = StateGraph(RobotProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('deploy', deploy_robot)
graph.add_edge('validate', 'deploy')
graph.add_edge('deploy', END)
graph.set_entry_point('validate')
graph = graph.compile()
