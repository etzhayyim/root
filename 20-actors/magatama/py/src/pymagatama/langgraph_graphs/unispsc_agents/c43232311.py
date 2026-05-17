from typing import TypedDict
from langgraph.graph import StateGraph, END

class DBState(TypedDict):
    license_type: str
    compliance_ok: bool
    deployment_model: str

def validate_license(state: DBState):
    state['compliance_ok'] = state['license_type'] in ['enterprise', 'perpetual']
    return {'compliance_ok': state['compliance_ok']}

def deploy_system(state: DBState):
    print(f'Deploying OODBMS to {state["deployment_model"]}')
    return {'deployment_model': state['deployment_model']}

graph = StateGraph(DBState)
graph.add_node('validate', validate_license)
graph.add_node('deploy', deploy_system)
graph.set_entry_point('validate')
graph.add_edge('validate', 'deploy')
graph.add_edge('deploy', END)
graph.compile()