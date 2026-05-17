from typing import TypedDict
from langgraph.graph import StateGraph, END

class RescueStationState(TypedDict):
    station_id: str
    specs: dict
    validation_passed: bool

def validate_specs(state: RescueStationState):
    required = ['fire_safety', 'power_capacity']
    passed = all(k in state['specs'] for k in required)
    return {'validation_passed': passed}

def deploy_station(state: RescueStationState):
    if state.get('validation_passed'):
        print(f'Deploying station {state['station_id']}')
    return {}

builder = StateGraph(RescueStationState)
builder.add_node('validate', validate_specs)
builder.add_node('deploy', deploy_station)
builder.set_entry_point('validate')
builder.add_edge('validate', 'deploy')
builder.add_edge('deploy', END)
graph = builder.compile()