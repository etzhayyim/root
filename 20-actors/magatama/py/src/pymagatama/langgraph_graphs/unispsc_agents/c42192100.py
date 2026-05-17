from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ClinicalChairState(TypedDict):
    spec_data: dict
    is_compliant: bool
    validation_errors: List[str]

def validate_medical_specs(state: ClinicalChairState):
    errors = []
    if not state['spec_data'].get('antimicrobial_cert'):
        errors.append('Missing antimicrobial certification')
    if state['spec_data'].get('weight_capacity', 0) < 150:
        errors.append('Weight capacity below clinical standards')
    return {'is_compliant': len(errors) == 0, 'validation_errors': errors}

graph = StateGraph(ClinicalChairState)
graph.add_node('validate', validate_medical_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()