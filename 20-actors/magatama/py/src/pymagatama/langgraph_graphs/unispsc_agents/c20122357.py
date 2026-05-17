from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class RobotJointState(TypedDict):
    part_id: str
    specs: dict
    validation_results: Annotated[list[str], operator.add]
    status: str

def validate_torque(state: RobotJointState) -> RobotJointState:
    torque = state['specs'].get('torque_rating_nm', 0)
    if torque > 0:
        state['validation_results'].append(f'Torque verified: {torque}Nm')
    return state

def validate_backlash(state: RobotJointState) -> RobotJointState:
    backlash = state['specs'].get('backlash_arcmin', 10)
    if backlash < 5:
        state['validation_results'].append(f'High-precision backlash: {backlash}arcmin')
    return state

def finalize_check(state: RobotJointState) -> RobotJointState:
    state['status'] = 'VALIDATED' if len(state['validation_results']) >= 2 else 'FAILED'
    return state

workflow = StateGraph(RobotJointState)
workflow.add_node('torque_check', validate_torque)
workflow.add_node('backlash_check', validate_backlash)
workflow.add_node('finalize', finalize_check)
workflow.set_entry_point('torque_check')
workflow.add_edge('torque_check', 'backlash_check')
workflow.add_edge('backlash_check', 'finalize')
workflow.add_edge('finalize', END)
graph = workflow.compile()