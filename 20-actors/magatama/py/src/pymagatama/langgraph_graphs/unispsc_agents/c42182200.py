from typing import TypedDict, List
from langgraph.graph import StateGraph

class MedicalState(TypedDict):
    device_specs: dict
    compliance_docs: List[str]
    validation_passed: bool

def validate_compliance(state: MedicalState):
    required = ['ISO 13485', 'Calibration Report']
    docs = state.get('compliance_docs', [])
    passed = all(doc in docs for doc in required)
    return {'validation_passed': passed}

def route_verification(state: MedicalState):
    return 'check' if not state['validation_passed'] else 'complete'

graph = StateGraph(MedicalState)
graph.add_node('check', validate_compliance)
graph.set_entry_point('check')
graph.set_finish_point('complete')
graph.add_edge('check', 'complete')
compiled_graph = graph.compile()