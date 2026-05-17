from typing import TypedDict
from langgraph.graph import StateGraph, END

class PumpState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_compliant: bool

def validate_nfpa_standards(state: PumpState):
    errors = []
    if not state['spec_data'].get('nfpa_20_certified'):
        errors.append('Missing NFPA 20 certification')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def route_by_compliance(state: PumpState):
    return 'compliant' if state['is_compliant'] else 'non_compliant'

graph = StateGraph(PumpState)
graph.add_node('validate', validate_nfpa_standards)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()