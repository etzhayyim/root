from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class ActuatorState(TypedDict):
    spec_requirements: dict
    validation_results: Annotated[list[str], operator.add]
    is_approved: bool

def validate_torque_specs(state: ActuatorState) -> ActuatorState:
    torque = state['spec_requirements'].get('torque_rating_nm', 0)
    if torque < 0.5:
        state['validation_results'].append('Torque below industrial baseline.')
        state['is_approved'] = False
    return state

def check_compliance(state: ActuatorState) -> ActuatorState:
    if 'certification_iso' not in state['spec_requirements']:
        state['validation_results'].append('Missing ISO certification.')
        state['is_approved'] = False
    return state

builder = StateGraph(ActuatorState)
builder.add_node('torque_check', validate_torque_specs)
builder.add_node('compliance_check', check_compliance)
builder.add_edge('torque_check', 'compliance_check')
builder.add_edge('compliance_check', END)
builder.set_entry_point('torque_check')
graph = builder.compile()
