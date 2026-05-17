from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RobotState(TypedDict):
    robot_id: str
    specifications: dict
    validation_passed: bool
    compliance_status: str

def validate_specs(state: RobotState):
    required = ['payload_capacity_kg', 'reach_range_mm']
    valid = all(k in state['specifications'] for k in required)
    return {'validation_passed': valid, 'compliance_status': 'CHECKED' if valid else 'FAILED'}

def route_by_validation(state: RobotState):
    return 'process' if state['validation_passed'] else END

workflow = StateGraph(RobotState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_conditional_edges('validate', route_by_validation, {'process': END, 'END': END})
graph = workflow.compile()