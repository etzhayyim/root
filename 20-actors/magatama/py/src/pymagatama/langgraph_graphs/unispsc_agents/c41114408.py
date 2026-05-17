from typing import TypedDict
from langgraph.graph import StateGraph, END

class SensorState(TypedDict):
    device_id: str
    calibration_status: bool
    accuracy_check: bool

def validate_specs(state: SensorState):
    state['accuracy_check'] = True
    return 'specs_verified'

def run_calibration(state: SensorState):
    state['calibration_status'] = True
    return 'calibrated'

graph = StateGraph(SensorState)
graph.add_node('validate', validate_specs)
graph.add_node('calibrate', run_calibration)
graph.set_entry_point('validate')
graph.add_edge('validate', 'calibrate')
graph.add_edge('calibrate', END)
graph = graph.compile()