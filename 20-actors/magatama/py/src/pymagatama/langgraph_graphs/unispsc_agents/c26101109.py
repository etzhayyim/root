from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MotorState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: MotorState):
    errors = []
    if state['spec_data'].get('voltage', 0) <= 0:
        errors.append('Invalid voltage')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

workflow = StateGraph(MotorState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()