from typing import TypedDict
from langgraph.graph import StateGraph, END

class PlethysmographState(TypedDict):
    device_id: str
    calibration_status: bool
    compliance_check: bool

def validate_calibration(state: PlethysmographState):
    state['calibration_status'] = True
    return 'calibration_verified'

def check_medical_compliance(state: PlethysmographState):
    state['compliance_check'] = True
    return 'compliance_verified'

workflow = StateGraph(PlethysmographState)
workflow.add_node('calibrate', validate_calibration)
workflow.add_node('compliance', check_medical_compliance)
workflow.set_entry_point('calibrate')
workflow.add_edge('calibrate', 'compliance')
workflow.add_edge('compliance', END)
graph = workflow.compile()