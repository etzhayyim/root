from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SensorState(TypedDict):
    sensor_id: str
    spec_data: dict
    validation_passed: bool
    is_dual_use: bool

def validate_specs(state: SensorState):
    specs = state.get('spec_data', {})
    # Check for industrial logic parameters
    passed = all(k in specs for k in ['range', 'voltage', 'ip_rating'])
    state['validation_passed'] = passed
    return state

def determine_export_control(state: SensorState):
    # Logic for high-precision sensors
    freq = state['spec_data'].get('switching_frequency', 0)
    state['is_dual_use'] = freq > 5000
    return state

graph = StateGraph(SensorState)
graph.add_node('validate', validate_specs)
graph.add_node('export_check', determine_export_control)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph = graph.compile()