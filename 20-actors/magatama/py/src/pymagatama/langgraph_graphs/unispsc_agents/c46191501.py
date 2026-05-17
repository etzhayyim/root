from typing import TypedDict
from langgraph.graph import StateGraph, END

class SmokeDetectorState(TypedDict):
    model_id: str
    compliance_certs: list
    sensitivity_test_result: float
    status: str

def validate_certification(state: SmokeDetectorState):
    required = ['UL217', 'EN14604']
    valid = all(cert in state['compliance_certs'] for cert in required)
    return {'status': 'CERTIFIED' if valid else 'FAILED_CERTIFICATION'}

def process_sensitivity(state: SmokeDetectorState):
    if state['sensitivity_test_result'] < 0.05:
        return {'status': 'PASSED_CALIBRATION'}
    return {'status': 'FAILED_CALIBRATION'}

graph = StateGraph(SmokeDetectorState)
graph.add_node('validate_cert', validate_certification)
graph.add_node('test_sensor', process_sensitivity)
graph.set_entry_point('validate_cert')
graph.add_edge('validate_cert', 'test_sensor')
graph.add_edge('test_sensor', END)
compile = graph.compile()