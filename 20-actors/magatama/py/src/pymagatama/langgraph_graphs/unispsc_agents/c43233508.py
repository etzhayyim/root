from typing import TypedDict
from langgraph.graph import StateGraph, END

class SoftwareState(TypedDict):
    app_bundle_id: str
    os_version: str
    security_check_passed: bool
    deployment_ready: bool

def validate_bundle(state: SoftwareState):
    state['security_check_passed'] = state['app_bundle_id'].startswith('com.carrier.')
    return state

def check_deployment(state: SoftwareState):
    state['deployment_ready'] = state['security_check_passed']
    return state

graph = StateGraph(SoftwareState)
graph.add_node('validation', validate_bundle)
graph.add_node('deployment', check_deployment)
graph.add_edge('validation', 'deployment')
graph.add_edge('deployment', END)
graph.set_entry_point('validation')
graph = graph.compile()
