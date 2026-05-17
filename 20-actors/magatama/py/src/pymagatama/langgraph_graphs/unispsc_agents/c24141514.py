from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PackagingState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_film_specs(state: PackagingState):
    errors = []
    if state['spec_data'].get('thickness', 0) <= 0:
        errors.append('Invalid thickness value')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

workflow = StateGraph(PackagingState)
workflow.add_node('validate', validate_film_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()