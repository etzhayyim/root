from typing import TypedDict
from langgraph.graph import StateGraph, END

class SolarLampState(TypedDict):
    specs: dict
    validated: bool
    error: str

def validate_specs(state: SolarLampState):
    required = ['IP_rating', 'battery_capacity']
    if all(k in state['specs'] for k in required):
        return {'validated': True}
    return {'validated': False, 'error': 'Missing core specs'}

def deploy_lamp(state: SolarLampState):
    return {'status': 'Ready for Procurement'}

graph = StateGraph(SolarLampState)
graph.add_node('validate', validate_specs)
graph.add_node('deploy', deploy_lamp)
graph.set_entry_point('validate')
graph.add_edge('validate', 'deploy')
graph.add_edge('deploy', END)
app = graph.compile()