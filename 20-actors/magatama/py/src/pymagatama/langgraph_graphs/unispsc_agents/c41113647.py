from typing import TypedDict
from langgraph.graph import StateGraph, END

class CalibratorState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_compliant: bool

def validate_frequency(state: CalibratorState):
    errors = []
    if 'accuracy' not in state['spec_data']: errors.append('Missing accuracy')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def check_traceability(state: CalibratorState):
    has_cert = state['spec_data'].get('has_calibration_cert', False)
    return {'is_compliant': state['is_compliant'] and has_cert}

graph = StateGraph(CalibratorState)
graph.add_node('validate', validate_frequency)
graph.add_node('traceability', check_traceability)
graph.set_entry_point('validate')
graph.add_edge('validate', 'traceability')
graph.add_edge('traceability', END)
graph = graph.compile()