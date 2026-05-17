from typing import TypedDict
from langgraph.graph import StateGraph, END

class State(TypedDict):
    spec: dict
    validated: bool
    error: str

def validate_treadmill_specs(state: State):
    required = ['motor_horsepower', 'safety_emergency_stop_mechanism']
    if all(k in state['spec'] for k in required):
        return {'validated': True}
    return {'validated': False, 'error': 'Missing core safety/power specifications'}

def deploy_procurement(state: State):
    print('Proceeding to procurement workflow')
    return {'validated': True}

graph = StateGraph(State)
graph.add_node('validate', validate_treadmill_specs)
graph.add_node('deploy', deploy_procurement)
graph.add_edge('validate', 'deploy')
graph.set_entry_point('validate')
graph.add_edge('deploy', END)
graph = graph.compile()