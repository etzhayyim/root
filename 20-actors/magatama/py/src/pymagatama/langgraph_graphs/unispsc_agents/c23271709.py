from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class WeldingGeneratorState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: WeldingGeneratorState):
    errors = []
    required_fields = ['rated_current', 'duty_cycle', 'safety_cert']
    for field in required_fields:
        if field not in state['spec_data']:
            errors.append(f'Missing {field}')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

workflow = StateGraph(WeldingGeneratorState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
