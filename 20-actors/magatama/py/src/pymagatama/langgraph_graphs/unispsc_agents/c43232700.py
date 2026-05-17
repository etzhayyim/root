from typing import TypedDict
from langgraph.graph import StateGraph, END

class SoftwareState(TypedDict):
    network_config: dict
    security_valid: bool
    deployment_ready: bool

def validate_network_specs(state: SoftwareState):
    # Simulate validation logic for network apps
    state['security_valid'] = 'TLS' in state['network_config'].get('protocols', [])
    return state

def check_deployment_readiness(state: SoftwareState):
    state['deployment_ready'] = state.get('security_valid', False)
    return state

graph = StateGraph(SoftwareState)
graph.add_node("validate", validate_network_specs)
graph.add_node("check", check_deployment_readiness)
graph.set_entry_point("validate")
graph.add_edge("validate", "check")
graph.add_edge("check", END)
compiled_graph = graph.compile()