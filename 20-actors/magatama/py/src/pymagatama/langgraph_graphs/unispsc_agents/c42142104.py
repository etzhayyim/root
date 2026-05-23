from typing import TypedDict
from langgraph.graph import StateGraph, END

class HydrocollatorState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_compliant: bool

def validate_safety_specs(state: HydrocollatorState):
    errors = []
    if not state['spec_data'].get('ISO_13485'):
        errors.append('Missing ISO 13485 certification.')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def check_temp_range(state: HydrocollatorState):
    temp = state['spec_data'].get('Temperature_Accuracy_Range', 0)
    if temp > 2.0:
        state['validation_errors'].append('Temperature variance exceeds clinical limits.')
    return {'is_compliant': len(state['validation_errors']) == 0}

graph = StateGraph(HydrocollatorState)
graph.add_node('safety_check', validate_safety_specs)
graph.add_node('temp_check', check_temp_range)
graph.set_entry_point('safety_check')
graph.add_edge('safety_check', 'temp_check')
graph.add_edge('temp_check', END)
graph = graph.compile()
