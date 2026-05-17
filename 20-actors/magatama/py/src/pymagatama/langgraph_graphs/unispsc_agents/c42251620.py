from typing import TypedDict
from langgraph.graph import StateGraph, END

class RehabEquipmentState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_approved: bool

def validate_specs(state: RehabEquipmentState):
    errors = []
    if state['spec_data'].get('load_capacity', 0) < 150:
        errors.append('Insufficient load capacity for clinical use.')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

def route_by_validation(state: RehabEquipmentState):
    return 'approved' if state['is_approved'] else 'rejected'

graph = StateGraph(RehabEquipmentState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)