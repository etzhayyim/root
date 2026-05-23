from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DentalDiscState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_spec(state: DentalDiscState):
    errors = []
    if not state['spec_data'].get('fda_mdr_registration_number'):
        errors.append('Missing FDA/MDR registration')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def check_biocompatibility(state: DentalDiscState):
    certified = state['spec_data'].get('biocompatibility_certification', False)
    return {'is_compliant': certified and not state['validation_errors']}

graph = StateGraph(DentalDiscState)
graph.add_node('validate', validate_spec)
graph.add_node('biosafety', check_biocompatibility)
graph.add_edge('validate', 'biosafety')
graph.add_edge('biosafety', END)
graph.set_entry_point('validate')
graph = graph.compile()
