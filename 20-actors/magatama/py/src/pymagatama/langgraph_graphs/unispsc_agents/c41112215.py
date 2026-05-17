from typing import TypedDict
from langgraph.graph import StateGraph, END

class HumidityControlState(TypedDict):
    temp_range: float
    target_humidity: float
    is_calibrated: bool

def validate_specs(state: HumidityControlState):
    if state['temp_range'] < 0 or state['temp_range'] > 100:
        return {'status': 'invalid'}
    return {'status': 'valid'}

def process_controller(state: HumidityControlState):
    if state['is_calibrated']:
        return 'ready_for_deployment'
    return 'needs_calibration'

graph = StateGraph(HumidityControlState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_controller)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()