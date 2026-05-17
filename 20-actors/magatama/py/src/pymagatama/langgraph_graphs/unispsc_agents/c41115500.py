from typing import TypedDict
from langgraph.graph import StateGraph, END

class SoundEquipState(TypedDict):
    calibration_status: bool
    compliance_score: float
    spec_approved: bool

def validate_specs(state: SoundEquipState):
    state['spec_approved'] = state['compliance_score'] > 0.9
    return 'approved' if state['spec_approved'] else 'rejected'

def check_calibration(state: SoundEquipState):
    return 'verified' if state['calibration_status'] else 'pending'

graph = StateGraph(SoundEquipState)
graph.add_node('validate', validate_specs)
graph.add_node('calibrate', check_calibration)
graph.add_edge('calibrate', 'validate')
graph.set_entry_point('calibrate')
graph.add_edge('validate', END)
graph.compile()