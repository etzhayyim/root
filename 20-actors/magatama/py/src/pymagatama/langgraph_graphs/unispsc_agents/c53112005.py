from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MeasurementState(TypedDict):
    device_id: str
    precision_check: bool
    calibration_status: str

def validate_device(state: MeasurementState):
    state['precision_check'] = True
    state['calibration_status'] = 'verified'
    return state

def report_generation(state: MeasurementState):
    print(f'Device {state['device_id']} validated.')
    return {'calibration_status': 'finalized'}

graph = StateGraph(MeasurementState)
graph.add_node('validate', validate_device)
graph.add_node('report', report_generation)
graph.add_edge('validate', 'report')
graph.add_edge('report', END)
graph.set_entry_point('validate')
graph = graph.compile()