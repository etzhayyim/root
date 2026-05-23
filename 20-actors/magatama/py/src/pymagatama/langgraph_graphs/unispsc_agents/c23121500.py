from typing import TypedDict
from langgraph.graph import StateGraph, END

class RobotProcurementState(TypedDict):
    spec_data: dict
    validation_errors: list
    approval_status: bool

def validate_robot_specs(state: RobotProcurementState):
    errors = []
    if state['spec_data'].get('payload', 0) <= 0:
        errors.append('Invalid payload capacity')
    return {'validation_errors': errors}

def check_compliance(state: RobotProcurementState):
    is_compliant = len(state['validation_errors']) == 0
    return {'approval_status': is_compliant}

graph = StateGraph(RobotProcurementState)
graph.add_node('validate', validate_robot_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
