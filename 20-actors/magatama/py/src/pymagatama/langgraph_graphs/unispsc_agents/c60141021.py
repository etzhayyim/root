from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DiscState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: DiscState):
    errors = []
    if state['spec_data'].get('weight', 0) < 100: errors.append('Weight below regulation')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

workflow = StateGraph(DiscState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()