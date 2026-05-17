from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END

class TeachingAidState(TypedDict):
    spec_sheet: dict
    validation_errors: list
    is_approved: bool

def validate_cooling_specs(state: TeachingAidState):
    errors = []
    if 'voltage' not in state['spec_sheet']: errors.append('Missing voltage')
    if 'safety_cert' not in state['spec_sheet']: errors.append('Missing safety certification')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

def approval_check(state: TeachingAidState):
    return 'approved' if state['is_approved'] else 'rejected'

graph = StateGraph(TeachingAidState)
graph.add_node('validate', validate_cooling_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', approval_check, {'approved': END, 'rejected': END})
graph.compile()