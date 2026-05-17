from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PlanBookState(TypedDict):
    spec_data: dict
    validation_passed: bool
    errors: List[str]

def validate_specs(state: PlanBookState):
    errors = []
    if state['spec_data'].get('page_count', 0) < 50:
        errors.append('Page count is too low for annual planning.')
    return {'validation_passed': len(errors) == 0, 'errors': errors}

def finalize_order(state: PlanBookState):
    if state['validation_passed']:
        print('Printing order approved.')
    return {}

builder = StateGraph(PlanBookState)
builder.add_node('validate', validate_specs)
builder.add_node('finalize', finalize_order)
builder.add_edge('validate', 'finalize')
builder.add_edge('finalize', END)
builder.set_entry_point('validate')
graph = builder.compile()