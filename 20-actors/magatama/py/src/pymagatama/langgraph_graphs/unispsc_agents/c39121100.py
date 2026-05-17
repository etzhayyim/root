from typing import TypedDict
from langgraph.graph import StateGraph, END

class DistributionState(TypedDict):
    spec_data: dict
    validation_errors: list
    status: str

def validate_electrical_specs(state: DistributionState):
    errors = []
    if not state['spec_data'].get('voltage'): errors.append('Missing voltage')
    if not state['spec_data'].get('rating'): errors.append('Missing IP rating')
    return {'validation_errors': errors, 'status': 'validated' if not errors else 'rejected'}

workflow = StateGraph(DistributionState)
workflow.add_node('validator', validate_electrical_specs)
workflow.set_entry_point('validator')
workflow.add_edge('validator', END)
graph = workflow.compile()