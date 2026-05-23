from typing import TypedDict
from langgraph.graph import StateGraph, END

class WeighingScaleState(TypedDict):
    spec_data: dict
    validation_passed: bool
    error_log: list

def validate_specs(state: WeighingScaleState):
    specs = state['spec_data']
    errors = []
    if specs.get('maximum_capacity_kg', 0) <= 0:
        errors.append('Invalid capacity')
    return {'validation_passed': len(errors) == 0, 'error_log': errors}

workflow = StateGraph(WeighingScaleState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
