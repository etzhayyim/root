from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class POSState(TypedDict):
    terminal_id: str
    compliance_certs: List[str]
    status: str

def validate_compliance(state: POSState):
    required = {'PCI', 'EMV'}
    if required.issubset(set(state['compliance_certs'])):
        return {'status': 'CERTIFIED'}
    return {'status': 'REJECTED'}

def deploy_terminal(state: POSState):
    print(f'Deploying terminal {state['terminal_id']}')
    return {'status': 'DEPLOYED'}

graph = StateGraph(POSState)
graph.add_node('validate', validate_compliance)
graph.add_node('deploy', deploy_terminal)
graph.set_entry_point('validate')
graph.add_edge('validate', 'deploy')
graph.add_edge('deploy', END)
graph = graph.compile()
