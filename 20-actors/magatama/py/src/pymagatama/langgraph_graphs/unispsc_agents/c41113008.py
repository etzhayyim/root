from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ScintigraphyState(TypedDict):
    device_id: str
    calibration_compliant: bool
    validation_logs: List[str]

def validate_radiation_safety(state: ScintigraphyState):
    state['validation_logs'].append('Verifying radiation shielding compliance...')
    return {'calibration_compliant': True}

def check_dicom_protocols(state: ScintigraphyState):
    state['validation_logs'].append('Checking DICOM image transmission protocols...')
    return state

graph = StateGraph(ScintigraphyState)
graph.add_node('safety_check', validate_radiation_safety)
graph.add_node('dicom_validation', check_dicom_protocols)
graph.set_entry_point('safety_check')
graph.add_edge('safety_check', 'dicom_validation')
graph.add_edge('dicom_validation', END)
app = graph.compile()
