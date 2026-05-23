from typing import TypedDict
from langgraph.graph import StateGraph, END

class PLCState(TypedDict):
    license_key: str
    version: str
    compatibility_check: bool

def validate_license(state: PLCState) -> PLCState:
    state['compatibility_check'] = state.get('license_key', '').startswith('PLC-')
    return state

def deploy_config(state: PLCState) -> PLCState:
    print(f'Deploying version {state["version"]} to target PLC hardware.')
    return state

graph = StateGraph(PLCState)
graph.add_node('validate', validate_license)
graph.add_node('deploy', deploy_config)
graph.set_entry_point('validate')
graph.add_edge('validate', 'deploy')
graph.add_edge('deploy', END)
graph = graph.compile()
