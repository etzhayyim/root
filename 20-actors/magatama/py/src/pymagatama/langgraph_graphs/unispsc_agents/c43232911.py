from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SoftwareState(TypedDict):
    software_name: str
    protocol: str
    is_compliant: bool

def validate_protocol(state: SoftwareState):
    allowed = ['SSH', 'TN3270', 'Telnet']
    return {'is_compliant': state['protocol'] in allowed}

def process_deployment(state: SoftwareState):
    print(f'Deploying {state['software_name']} configuration...')
    return {'is_compliant': True}

graph = StateGraph(SoftwareState)
graph.add_node('validate', validate_protocol)
graph.add_node('deploy', process_deployment)
graph.set_entry_point('validate')
graph.add_edge('validate', 'deploy')
graph.add_edge('deploy', END)
graph = graph.compile()