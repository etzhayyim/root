from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class TorqueLimiterState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_safe: bool

def validate_torque_specs(state: TorqueLimiterState):
    errors = []
    if state['spec_data'].get('max_torque', 0) <= 0:
        errors.append('Invalid torque setting')
    return {'validation_errors': errors, 'is_safe': len(errors) == 0}

def approval_check(state: TorqueLimiterState):
    return 'approved' if state['is_safe'] else 'rejected'

graph = StateGraph(TorqueLimiterState)
graph.add_node('validate', validate_torque_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
