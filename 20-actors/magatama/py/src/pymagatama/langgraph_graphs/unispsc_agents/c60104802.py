from typing import TypedDict
from langgraph.graph import StateGraph, END

class WaveTankState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_compliant: bool

def validate_specs(state: WaveTankState):
    errors = []
    if state['spec_data'].get('max_wave_height', 0) > 5.0:
        errors.append('Wave height exceeds structural safety limit')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

workflow = StateGraph(WaveTankState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()