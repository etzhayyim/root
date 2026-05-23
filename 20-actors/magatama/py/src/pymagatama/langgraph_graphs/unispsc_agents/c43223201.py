from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class VoicePortalState(TypedDict):
    configuration: dict
    validation_errors: List[str]
    is_ready: bool

def validate_config(state: VoicePortalState):
    errors = []
    if 'encryption_protocol' not in state['configuration']:
        errors.append('Missing encryption_protocol')
    return {'validation_errors': errors}

def deploy_portal(state: VoicePortalState):
    if not state['validation_errors']:
        return {'is_ready': True}
    return {'is_ready': False}

graph = StateGraph(VoicePortalState)
graph.add_node('validate', validate_config)
graph.add_node('deploy', deploy_portal)
graph.set_entry_point('validate')
graph.add_edge('validate', 'deploy')
graph.add_edge('deploy', END)
app = graph.compile()
