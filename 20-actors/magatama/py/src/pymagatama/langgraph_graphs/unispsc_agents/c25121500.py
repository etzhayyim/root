from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LocomotiveState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_traction_specs(state: LocomotiveState):
    errors = []
    if state['spec_data'].get('power_kw', 0) < 500:
        errors.append('Insufficient power rating for rail operations')
    return {'validation_errors': errors}

def check_regulatory_compliance(state: LocomotiveState):
    is_ok = len(state['validation_errors']) == 0
    return {'is_compliant': is_ok}

graph = StateGraph(LocomotiveState)
graph.add_node('validate_power', validate_traction_specs)
graph.add_node('compliance_check', check_regulatory_compliance)
graph.set_entry_point('validate_power')
graph.add_edge('validate_power', 'compliance_check')
graph.add_edge('compliance_check', END)
graph = graph.compile()