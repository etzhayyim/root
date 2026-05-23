from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SensorState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_sensor_specs(state: SensorState):
    errors = []
    if 'ip_rating' not in state['spec_data']:
        errors.append('Missing IP protection rating.')
    state['validation_errors'] = errors
    state['approved'] = len(errors) == 0
    return state

def route_by_validation(state: SensorState):
    return 'approved' if state['approved'] else 'rejected'

graph = StateGraph(SensorState)
graph.add_node('validate', validate_sensor_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
