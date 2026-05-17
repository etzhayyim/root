from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class IonMeterState(TypedDict):
    device_id: str
    calibration_data: dict
    validation_status: str

def validate_calibration(state: IonMeterState):
    data = state.get('calibration_data', {})
    status = 'PASS' if data.get('drift') < 0.05 else 'FAIL'
    return {'validation_status': status}

def route_by_status(state: IonMeterState):
    return 'end' if state['validation_status'] == 'PASS' else 'end'

graph = StateGraph(IonMeterState)
graph.add_node('validate', validate_calibration)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()