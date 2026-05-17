from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class HumiditySpecState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_sensor_specs(state: HumiditySpecState):
    errors = []
    if state['spec_data'].get('range', 0) > 100: errors.append('Range exceeds 100%')
    return {'validation_errors': errors}

def approve_procurement(state: HumiditySpecState):
    return {'approved': len(state['validation_errors']) == 0}

graph = StateGraph(HumiditySpecState)
graph.add_node('validate', validate_sensor_specs)
graph.add_node('approve', approve_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()