from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MiningSupportState(TypedDict):
    props: List[dict]
    status: str
    validation_errors: List[str]

def validate_timber_specs(state: MiningSupportState):
    errors = []
    for prop in state['props']:
        if prop.get('moisture_content_percentage', 0) > 20:
            errors.append(f'High moisture: {prop['id']}')
    return {'validation_errors': errors, 'status': 'validated' if not errors else 'failed'}

def structural_integrity_check(state: MiningSupportState):
    if state['status'] == 'failed':
        return {'status': 'rejected'}
    return {'status': 'approved'}

builder = StateGraph(MiningSupportState)
builder.add_node('validate', validate_timber_specs)
builder.add_node('integrity', structural_integrity_check)
builder.add_edge('validate', 'integrity')
builder.add_edge('integrity', END)
builder.set_entry_point('validate')
graph = builder.compile()