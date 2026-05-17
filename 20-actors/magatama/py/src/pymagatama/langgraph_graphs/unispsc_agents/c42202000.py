from typing import TypedDict
from langgraph.graph import StateGraph, END

class GammaCameraState(TypedDict):
    device_id: str
    calibration_status: bool
    compliance_docs: list
    is_validated: bool

def validate_compliance(state: GammaCameraState):
    # Simulated technical validation workflow for Gamma systems
    required_docs = {'DICOM', 'RadiationSafety', 'CalibrationCert'}
    has_docs = all(doc in state['compliance_docs'] for doc in required_docs)
    return {'is_validated': has_docs}

def approval_check(state: GammaCameraState):
    return 'approved' if state['is_validated'] else 'rejected'

graph = StateGraph(GammaCameraState)
graph.add_node('validate', validate_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()