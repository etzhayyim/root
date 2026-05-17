from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MegohmmeterState(TypedDict):
    instrument_id: str
    test_voltage: float
    has_calibration_cert: bool
    validation_status: str

def validate_spec(state: MegohmmeterState):
    if state['test_voltage'] < 500:
        return {'validation_status': 'REQUIRES_REVIEW'}
    return {'validation_status': 'APPROVED'}

def audit_cert(state: MegohmmeterState):
    if not state['has_calibration_cert']:
        return {'validation_status': 'REJECTED'}
    return {'validation_status': 'APPROVED'}

graph = StateGraph(MegohmmeterState)
graph.add_node('validate', validate_spec)
graph.add_node('audit', audit_cert)
graph.add_edge('validate', 'audit')
graph.add_edge('audit', END)
graph.set_entry_point('validate')
graph = graph.compile()