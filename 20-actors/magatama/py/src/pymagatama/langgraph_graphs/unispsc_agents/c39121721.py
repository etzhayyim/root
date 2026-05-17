from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class InsulatorState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_insulator_specs(state: InsulatorState):
    errors = []
    required_fields = ['Dielectric Strength', 'Material', 'Standards']
    for field in required_fields:
        if field not in state['spec_data']:
            errors.append(f'Missing mandatory field: {field}')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

workflow = StateGraph(InsulatorState)
workflow.add_node('validate', validate_insulator_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()