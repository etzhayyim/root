from typing import TypedDict
from langgraph.graph import StateGraph, END

class SensorState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_specs(state: SensorState):
    specs = state['spec_data']
    required = ['resolution', 'ip_rating']
    state['validation_passed'] = all(k in specs for k in required)
    return state

graph = StateGraph(SensorState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()