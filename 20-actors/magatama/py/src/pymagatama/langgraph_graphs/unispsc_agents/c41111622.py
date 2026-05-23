from typing import TypedDict
from langgraph.graph import StateGraph, END

class MeasurementState(TypedDict):
    device_id: str
    resolution: float
    accuracy_check: bool
    calibration_status: str

def validate_specs(state: MeasurementState):
    if state['resolution'] <= 0.001:
        return {'accuracy_check': True}
    return {'accuracy_check': False}

def update_records(state: MeasurementState):
    return {'calibration_status': 'verified'}

graph = StateGraph(MeasurementState)
graph.add_node('validate', validate_specs)
graph.add_node('record', update_records)
graph.add_edge('validate', 'record')
graph.add_edge('record', END)
graph.set_entry_point('validate')
graph = graph.compile()
