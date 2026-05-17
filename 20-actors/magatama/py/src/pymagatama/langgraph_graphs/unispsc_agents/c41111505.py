from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class AuditState(TypedDict):
    weight_set_id: str
    oiml_class: str
    calibration_status: bool
    errors: List[str]

def validate_oiml_compliance(state: AuditState):
    if state['oiml_class'] not in ['E1', 'E2', 'F1', 'F2', 'M1']:
        state['errors'].append('Invalid OIML class')
    return state

def check_calibration_certificate(state: AuditState):
    if not state['calibration_status']:
        state['errors'].append('Missing valid calibration certificate')
    return state

graph = StateGraph(AuditState)
graph.add_node('validate', validate_oiml_compliance)
graph.add_node('certify', check_calibration_certificate)
graph.set_entry_point('validate')
graph.add_edge('validate', 'certify')
graph.add_edge('certify', END)
graph = graph.compile()