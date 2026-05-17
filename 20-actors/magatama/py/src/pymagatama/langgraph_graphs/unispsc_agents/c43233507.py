from typing import TypedDict
from langgraph.graph import StateGraph, END

class SoftwareState(TypedDict):
    requirements: dict
    validation_errors: list
    status: str

def validate_tech_specs(state: SoftwareState):
    errors = []
    if 'network_protocol' not in state['requirements']: errors.append('Missing protocol')
    return {'validation_errors': errors}

def deploy_config(state: SoftwareState):
    return {'status': 'READY_FOR_DEPLOY' if not state['validation_errors'] else 'ERROR'}

graph = StateGraph(SoftwareState)
graph.add_node('validate', validate_tech_specs)
graph.add_node('deploy', deploy_config)
graph.set_entry_point('validate')
graph.add_edge('validate', 'deploy')
graph.add_edge('deploy', END)
graph = graph.compile()