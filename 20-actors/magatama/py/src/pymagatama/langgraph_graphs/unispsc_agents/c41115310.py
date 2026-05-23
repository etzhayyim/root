from typing import TypedDict
from langgraph.graph import StateGraph, END

class CalibrationState(TypedDict):
    spec_data: dict
    calibration_status: str
    validation_errors: list

def validate_specs(state: CalibrationState):
    errors = []
    if 'traceability' not in state['spec_data']:
        errors.append('Missing NIST/ISO traceability certification')
    return {'validation_errors': errors}

def route_verification(state: CalibrationState):
    return 'validate' if not state['validation_errors'] else END

graph = StateGraph(CalibrationState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
