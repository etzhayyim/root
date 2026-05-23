from typing import TypedDict
from langgraph.graph import StateGraph, END

class DialysisState(TypedDict):
    device_id: str
    calibration_data: dict
    compliance_verified: bool

def validate_controller(state: DialysisState):
    # Simulate regulatory validation logic
    state['compliance_verified'] = state.get('calibration_data', {}).get('precision') > 0.95
    return state

def approval_check(state: DialysisState):
    return 'approved' if state['compliance_verified'] else 'rejected'

graph = StateGraph(DialysisState)
graph.add_node('validate', validate_controller)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()
