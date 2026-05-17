from typing import TypedDict
from langgraph.graph import StateGraph, END

class CRRTState(TypedDict):
    device_id: str
    compliance_docs: list[str]
    validation_status: bool

def validate_compliance(state: CRRTState):
    # Simulate regulatory validation logic
    state['validation_status'] = len(state['compliance_docs']) >= 2
    return state

def check_calibration(state: CRRTState):
    print(f'Checking calibration for device {state['device_id']}')
    return state

graph = StateGraph(CRRTState)
graph.add_node('validate', validate_compliance)
graph.add_node('calibrate', check_calibration)
graph.set_entry_point('validate')
graph.add_edge('validate', 'calibrate')
graph.add_edge('calibrate', END)
graph = graph.compile()