from typing import TypedDict
from langgraph.graph import StateGraph, END

class RadiationGearState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_lead_equivalent(state: RadiationGearState):
    equiv = state['spec_data'].get('lead_equiv', 0)
    state['validation_passed'] = equiv >= 0.5
    return state

def verify_medical_cert(state: RadiationGearState):
    certs = state['spec_data'].get('certs', [])
    state['validation_passed'] = state['validation_passed'] and 'IEC61331' in certs
    return state

graph = StateGraph(RadiationGearState)
graph.add_node('lead_check', validate_lead_equivalent)
graph.add_node('cert_check', verify_medical_cert)
graph.set_entry_point('lead_check')
graph.add_edge('lead_check', 'cert_check')
graph.add_edge('cert_check', END)
graph = graph.compile()
