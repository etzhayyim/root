from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ExtensometerState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_calibration(state: ExtensometerState):
    errors = []
    if 'iso9513' not in state['spec_data'].get('certs', []):
        errors.append('Calibration must meet ISO 9513 standards.')
    return {'validation_errors': errors}

def final_check(state: ExtensometerState):
    is_compliant = len(state['validation_errors']) == 0
    return {'is_compliant': is_compliant}

graph = StateGraph(ExtensometerState)
graph.add_node('validate_calibration', validate_calibration)
graph.add_node('final_check', final_check)
graph.set_entry_point('validate_calibration')
graph.add_edge('validate_calibration', 'final_check')
graph.add_edge('final_check', END)
graph = graph.compile()