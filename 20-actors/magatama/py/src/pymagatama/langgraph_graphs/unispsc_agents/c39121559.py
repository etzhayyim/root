from typing import TypedDict
from langgraph.graph import StateGraph, END

class SwitchState(TypedDict):
    spec: dict
    validated: bool
    error: str

def validate_specs(state: SwitchState):
    required = ['load_capacity', 'voltage', 'ip_rating']
    if all(k in state['spec'] for k in required):
        return {'validated': True}
    return {'validated': False, 'error': 'Missing mandatory specs'}

def deploy_logic(state: SwitchState):
    return {'validated': True}

graph = StateGraph(SwitchState)
graph.add_node('validate', validate_specs)
graph.add_node('deploy', deploy_logic)
graph.set_entry_point('validate')
graph.add_edge('validate', 'deploy')
graph.add_edge('deploy', END)
graph = graph.compile()
