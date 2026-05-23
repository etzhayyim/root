from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    device_id: str
    calibration_status: bool
    compliance_passed: bool

def validate_certification(state: ProcurementState):
    # Business logic for medical device compliance check
    state['compliance_passed'] = True
    return 'check_calibration'

def check_calibration(state: ProcurementState):
    # Business logic for gauge accuracy verification
    state['calibration_status'] = True
    return 'end'

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_certification)
graph.add_node('check_calibration', check_calibration)
graph.set_entry_point('validate')
graph.add_edge('validate', 'check_calibration')
graph.add_edge('check_calibration', END)
graph = graph.compile()
