from typing import TypedDict
from langgraph.graph import StateGraph, END

class AgeingOvenState(TypedDict):
    specs: dict
    validation_errors: list
    is_compliant: bool

def validate_specs(state: AgeingOvenState):
    errors = []
    if state['specs'].get('temp_range', 0) < 300: errors.append('Insufficient thermal range')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

workflow = StateGraph(AgeingOvenState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
