from typing import TypedDict
from langgraph.graph import StateGraph, END

class DeionizationState(TypedDict):
    flow_rate: float
    resistivity: float
    status: str

def validate_specs(state: DeionizationState):
    if state['resistivity'] < 18.2:
        return {'status': 'Sub-standard'}
    return {'status': 'Certified'}

def deploy_equipment(state: DeionizationState):
    print(f'Deploying unit with {state['flow_rate']} L/h capacity.')
    return {'status': 'Deployed'}

graph = StateGraph(DeionizationState)
graph.add_node('validate', validate_specs)
graph.add_node('deploy', deploy_equipment)
graph.set_entry_point('validate')
graph.add_edge('validate', 'deploy')
graph.add_edge('deploy', END)
graph = graph.compile()