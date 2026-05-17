from typing import TypedDict
from langgraph.graph import StateGraph, END

class RobotState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_compliant: bool

def validate_robot_specs(state: RobotState):
    errors = []
    if state['spec_data'].get('payload', 0) <= 0:
        errors.append('Invalid payload capacity')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def route_by_validation(state: RobotState):
    return 'process' if state['is_compliant'] else 'reject'

graph = StateGraph(RobotState)
graph.add_node('validate', validate_robot_specs)
graph.add_conditional_edges('validate', route_by_validation, {'process': 'process', 'reject': END})
graph.add_node('process', lambda s: {'spec_data': s['spec_data']})
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()