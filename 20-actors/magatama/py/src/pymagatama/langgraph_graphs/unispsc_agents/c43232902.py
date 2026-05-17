from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ServerState(TypedDict):
    requirements: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: ServerState):
    # Simulate CAD/Spec validation logic for comms software
    errors = []
    if 'encryption' not in state['requirements']: errors.append('Missing encryption specs')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def deploy_config(state: ServerState):
    return {'is_compliant': True}

graph = StateGraph(ServerState)
graph.add_node('validate', validate_specs)
graph.add_node('deploy', deploy_config)
graph.set_entry_point('validate')
graph.add_edge('validate', 'deploy')
graph.add_edge('deploy', END)
graph = graph.compile()