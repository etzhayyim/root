from typing import TypedDict
from langgraph.graph import StateGraph, END

class OSState(TypedDict):
    license_key: str
    version: str
    compliance_check: bool

def validate_license(state: OSState):
    state['compliance_check'] = state['license_key'].startswith('OS-')
    return 'license_checked'

def deploy_os(state: OSState):
    return {'status': 'deployed'}

graph = StateGraph(OSState)
graph.add_node('validate', validate_license)
graph.add_node('deploy', deploy_os)
graph.set_entry_point('validate')
graph.add_edge('validate', 'deploy')
graph.add_edge('deploy', END)
graph = graph.compile()