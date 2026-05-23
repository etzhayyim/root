from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    spec_data: dict
    validation_status: str

def validate_medical_grade(state: ProcurementState):
    compliance = state['spec_data'].get('iso_cert')
    return {'validation_status': 'passed' if compliance else 'failed'}

def check_compression(state: ProcurementState):
    pressure = state['spec_data'].get('compression_mmhg', 0)
    status = 'approved' if 15 <= pressure <= 30 else 'rejected'
    return {'validation_status': status}

graph = StateGraph(ProcurementState)
graph.add_node('validate_iso', validate_medical_grade)
graph.add_node('check_pressure', check_compression)
graph.set_entry_point('validate_iso')
graph.add_edge('validate_iso', 'check_pressure')
graph.add_edge('check_pressure', END)
graph = graph.compile()
