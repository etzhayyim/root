from typing import TypedDict
from langgraph.graph import StateGraph, END

class SoftwareState(TypedDict):
    license_key: str
    compliance_checked: bool
    deployment_ready: bool

def validate_licensing(state: SoftwareState):
    state['compliance_checked'] = True
    return 'licensing_verified'

def check_deployment_env(state: SoftwareState):
    state['deployment_ready'] = True
    return 'env_ready'

graph = StateGraph(SoftwareState)
graph.add_node('validate', validate_licensing)
graph.add_node('deploy', check_deployment_env)
graph.add_edge('validate', 'deploy')
graph.add_edge('deploy', END)
graph.set_entry_point('validate')
graph = graph.compile()