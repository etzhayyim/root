from typing import TypedDict
from langgraph.graph import StateGraph, END

class DialysateGraphState(TypedDict):
    device_id: str
    calibration_data: dict
    compliance_score: float
    status: str

def validate_calibration(state: DialysateGraphState):
    # Simulate logic to verify calibration certificate
    return {'status': 'CERTIFIED' if state['calibration_data'].get('valid') else 'REJECTED'}

def check_compliance(state: DialysateGraphState):
    # Simulate regulatory check
    return {'compliance_score': 0.98 if state['status'] == 'CERTIFIED' else 0.0}

graph = StateGraph(DialysateGraphState)
graph.add_node('validate', validate_calibration)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
app = graph.compile()