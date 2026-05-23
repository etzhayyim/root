from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class State(TypedDict):
    device_id: str
    calibration_status: bool
    compliance_docs: List[str]
    approved: bool

def validate_medical_cert(state: State) -> State:
    if 'ISO_13485' in state['compliance_docs']:
        state['approved'] = True
    return state

def check_calibration(state: State) -> State:
    state['calibration_status'] = True
    return state

graph = StateGraph(State)
graph.add_node('cert_check', validate_medical_cert)
graph.add_node('cal_check', check_calibration)
graph.set_entry_point('cert_check')
graph.add_edge('cert_check', 'cal_check')
graph.add_edge('cal_check', END)
graph = graph.compile()
