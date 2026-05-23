from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class RobotJointState(TypedDict):
    part_id: str
    spec: dict
    validation_log: List[str]
    is_approved: bool

def validate_torque_specs(state: RobotJointState):
    spec = state['spec']
    if spec.get('rated_torque_nm', 0) > 500:
        state['validation_log'].append('High torque load detected: manual safety review required.')
    return {'validation_log': state['validation_log']}

def check_certification(state: RobotJointState):
    cert = state['spec'].get('certification_standard')
    state['is_approved'] = cert is not None
    return {'is_approved': state['is_approved']}

builder = StateGraph(RobotJointState)
builder.add_node('validate_torque', validate_torque_specs)
builder.add_node('check_cert', check_certification)
builder.add_edge('validate_torque', 'check_cert')
builder.add_edge('check_cert', END)
builder.set_entry_point('validate_torque')
graph = builder.compile()
