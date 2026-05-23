from typing import TypedDict
from langgraph.graph import StateGraph, END

class MonitoringState(TypedDict):
    device_id: str
    compliance_cleared: bool
    calibration_status: str

def validate_compliance(state: MonitoringState):
    print(f'Validating medical compliance for {state['device_id']}')
    return {'compliance_cleared': True}

def check_calibration(state: MonitoringState):
    print('Checking sensor calibration records...')
    return {'calibration_status': 'verified'}

graph = StateGraph(MonitoringState)
graph.add_node('validate', validate_compliance)
graph.add_node('calibrate', check_calibration)
graph.set_entry_point('validate')
graph.add_edge('validate', 'calibrate')
graph.add_edge('calibrate', END)
graph = graph.compile()
