from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class RobotJointState(TypedDict):
    joint_id: str
    spec_data: dict
    validation_logs: Annotated[Sequence[str], operator.add]
    is_approved: bool

def validate_joint_specs(state: RobotJointState):
    specs = state['spec_data']
    logs = []
    if specs.get('torque_capacity_nm', 0) <= 0:
        logs.append('Invalid torque capacity')
    return {'validation_logs': logs}

def check_compliance(state: RobotJointState):
    is_compliant = len(state['validation_logs']) == 0
    return {'is_approved': is_compliant}

graph = StateGraph(RobotJointState)
graph.add_node('validate', validate_joint_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
