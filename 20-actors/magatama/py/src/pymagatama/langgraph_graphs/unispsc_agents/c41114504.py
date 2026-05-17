from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class PitchGraphState(TypedDict):
    instrument_type: str
    spec_data: dict
    validation_passed: bool
    errors: List[str]

def validate_specs(state: PitchGraphState):
    errors = []
    if state['spec_data'].get('accuracy_tolerance', 0) > 0.05:
        errors.append('Tolerance exceeds precision requirements.')
    return {'validation_passed': len(errors) == 0, 'errors': errors}

def route_verification(state: PitchGraphState):
    return 'valid' if state['validation_passed'] else 'flag_manual_review'

graph = StateGraph(PitchGraphState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()