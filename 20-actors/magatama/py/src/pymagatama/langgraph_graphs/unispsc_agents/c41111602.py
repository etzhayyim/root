from typing import TypedDict
from langgraph.graph import StateGraph, END

class PedometerState(TypedDict):
    device_id: str
    sensor_accuracy: float
    compliance_docs: list
    status: str

def validate_sensor_accuracy(state: PedometerState):
    if state['sensor_accuracy'] < 0.95:
        return {'status': 'rejected'}
    return {'status': 'pending_doc_check'}

def verify_compliance(state: PedometerState):
    if 'ISO_calibration' in state['compliance_docs']:
        return {'status': 'approved'}
    return {'status': 'needs_manual_review'}

graph = StateGraph(PedometerState)
graph.add_node('validate', validate_sensor_accuracy)
graph.add_node('compliance', verify_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
