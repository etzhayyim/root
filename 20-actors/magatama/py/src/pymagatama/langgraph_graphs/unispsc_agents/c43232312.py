from typing import TypedDict
from langgraph.graph import StateGraph, END

class PortalState(TypedDict):
    software_id: str
    compliance_checked: bool
    deployment_ready: bool

def validate_license(state: PortalState):
    print(f'Validating license for {state['software_id']}')
    return {'compliance_checked': True}

def check_security(state: PortalState):
    print('Running security scans on portal architecture')
    return {'deployment_ready': True}

graph = StateGraph(PortalState)
graph.add_node('validate', validate_license)
graph.add_node('security', check_security)
graph.set_entry_point('validate')
graph.add_edge('validate', 'security')
graph.add_edge('security', END)
graph = graph.compile()
