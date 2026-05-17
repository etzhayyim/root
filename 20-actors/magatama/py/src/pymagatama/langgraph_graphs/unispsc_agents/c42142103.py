from typing import TypedDict
from langgraph.graph import StateGraph, END

class MedicalLampState(TypedDict):
    spec_data: dict
    approved: bool
    error_log: list

def validate_medical_specs(state: MedicalLampState):
    required = ['MedicalDeviceLicenseNumber', 'ComplianceStandardIEC60601']
    errors = [key for key in required if not state['spec_data'].get(key)]
    return {'approved': len(errors) == 0, 'error_log': errors}

graph = StateGraph(MedicalLampState)
graph.add_node('validate', validate_medical_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
compile_graph = graph.compile()