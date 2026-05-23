from typing import TypedDict
from langgraph.graph import StateGraph, END

class RobotSpecs(TypedDict):
    payload: float
    reach: float
    iso_compliance: bool

def validate_specs(state: RobotSpecs):
    if state['payload'] > 500:
        return {'status': 'heavy_duty_review'}
    return {'status': 'standard_check'}

def deploy_robot(state: RobotSpecs):
    return {'action': 'initiate_installation'}

graph = StateGraph(RobotSpecs)
graph.add_node('validate', validate_specs)
graph.add_node('deploy', deploy_robot)
graph.set_entry_point('validate')
graph.add_edge('validate', 'deploy')
graph.add_edge('deploy', END)
graph = graph.compile()
