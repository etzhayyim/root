from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SpringState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_spring_specs(state: SpringState):
    errors = []
    if state['spec_data'].get('load_capacity', 0) <= 0:
        errors.append('Invalid load capacity')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

def route_by_validation(state: SpringState):
    return 'approved' if state['is_approved'] else 'rejected'

graph = StateGraph(SpringState)
graph.add_node('validate', validate_spring_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
