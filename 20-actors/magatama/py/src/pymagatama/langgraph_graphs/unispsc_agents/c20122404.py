from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class RobotEndEffectorState(TypedDict):
    spec_requirements: dict
    validation_checks: List[str]
    approved: bool

def validate_gripper_specs(state: RobotEndEffectorState):
    checks = []
    if state['spec_requirements'].get('payload_capacity_kg', 0) > 0:
        checks.append('payload_validated')
    return {'validation_checks': checks}

def approve_procurement(state: RobotEndEffectorState):
    is_approved = 'payload_validated' in state['validation_checks']
    return {'approved': is_approved}

graph = StateGraph(RobotEndEffectorState)
graph.add_node('validate', validate_gripper_specs)
graph.add_node('approve', approve_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
app = graph.compile()