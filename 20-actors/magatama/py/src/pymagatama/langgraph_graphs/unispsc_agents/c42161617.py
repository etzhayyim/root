from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class DialysisMonitorState(TypedDict):
    device_id: str
    sensor_data: dict
    compliance_check: bool
    final_approval: bool

def validate_sensor_calibration(state: DialysisMonitorState):
    # Simulate validation logic for arterial pressure sensor accuracy
    is_valid = state['sensor_data'].get('accuracy_rating', 0) > 0.95
    return {'compliance_check': is_valid}

def update_compliance_status(state: DialysisMonitorState):
    approval = state['compliance_check'] and state['device_id'].startswith('SN')
    return {'final_approval': approval}

graph = StateGraph(DialysisMonitorState)
graph.add_node('validate_sensors', validate_sensor_calibration)
graph.add_node('final_check', update_compliance_status)
graph.add_edge('validate_sensors', 'final_check')
graph.add_edge('final_check', END)
graph.set_entry_point('validate_sensors')
graph = graph.compile()