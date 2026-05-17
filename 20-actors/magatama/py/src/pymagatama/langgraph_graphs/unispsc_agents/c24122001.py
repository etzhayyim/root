from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ContainerState(TypedDict):
    bottle_type: str
    volume: float
    certification: List[str]
    approved: bool

def validate_specs(state: ContainerState):
    state['approved'] = state['volume'] > 0 and 'FDA' in state['certification']
    return state

def process_deployment(state: ContainerState):
    print(f'Processing {state['bottle_type']} for inventory.')
    return {'approved': True}

graph = StateGraph(ContainerState)
graph.add_node('validate', validate_specs)
graph.add_node('deploy', process_deployment)
graph.add_edge('validate', 'deploy')
graph.add_edge('deploy', END)
graph.set_entry_point('validate')
graph = graph.compile()