from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DialysisTubeState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_compliance(state: DialysisTubeState):
    errors = []
    if not state['spec_data'].get('sterility_cert'):
        errors.append('Missing sterility documentation')
    if not state['spec_data'].get('iso_10993_passed', False):
        errors.append('Biocompatibility validation failed')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

graph = StateGraph(DialysisTubeState)
graph.add_node('validate', validate_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
