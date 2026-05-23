from typing import TypedDict
from langgraph.graph import StateGraph, END

class StudyStandState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_approved: bool

def validate_specs(state: StudyStandState):
    errors = []
    if state['spec_data'].get('load_capacity', 0) < 2: errors.append('Load capacity too low')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

def decision_node(state: StudyStandState):
    return 'approved' if state['is_approved'] else 'rejected'

graph = StateGraph(StudyStandState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
