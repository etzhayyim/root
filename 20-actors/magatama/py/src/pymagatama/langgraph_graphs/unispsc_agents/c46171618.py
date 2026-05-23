from typing import TypedDict
from langgraph.graph import StateGraph, END

class DoorbellState(TypedDict):
    model: str
    connectivity: str
    is_verified: bool

def validate_specs(state: DoorbellState):
    if state['connectivity'] in ['wired', 'wireless']:
        return {'is_verified': True}
    return {'is_verified': False}

def process_deployment(state: DoorbellState):
    print(f'Deploying doorbell model: {state['model']}')
    return state

graph = StateGraph(DoorbellState)
graph.add_node('validate', validate_specs)
graph.add_node('deploy', process_deployment)
graph.set_entry_point('validate')
graph.add_edge('validate', 'deploy')
graph.add_edge('deploy', END)
graph = graph.compile()
