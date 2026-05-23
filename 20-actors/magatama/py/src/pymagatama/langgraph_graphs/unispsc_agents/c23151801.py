from typing import TypedDict
from langgraph.graph import StateGraph, END

class WeldingWorkflowState(TypedDict):
    equipment_id: str
    safety_check_passed: bool
    calibration_status: bool
    final_approval: bool

def validate_safety_protocols(state: WeldingWorkflowState):
    state['safety_check_passed'] = True
    return 'safety_validated'

def verify_calibration(state: WeldingWorkflowState):
    state['calibration_status'] = True
    return 'calibration_verified'

graph = StateGraph(WeldingWorkflowState)
graph.add_node('safety', validate_safety_protocols)
graph.add_node('calibration', verify_calibration)
graph.set_entry_point('safety')
graph.add_edge('safety', 'calibration')
graph.add_edge('calibration', END)
graph = graph.compile()
