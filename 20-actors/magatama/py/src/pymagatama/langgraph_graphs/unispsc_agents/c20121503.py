from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class ActuatorState(TypedDict):
    spec_data: dict
    validation_log: Annotated[Sequence[str], operator.add]
    is_approved: bool

def validate_torque(state: ActuatorState):
    torque = state['spec_data'].get('torque_rating_nm', 0)
    if torque > 0:
        return {'validation_log': ['Torque rating validated'], 'is_approved': True}
    return {'validation_log': ['Torque rating invalid'], 'is_approved': False}

def check_compliance(state: ActuatorState):
    compliance = state['spec_data'].get('compliance_certification', '')
    if 'ISO' in compliance:
        return {'validation_log': ['Compliance standard met']}
    return {'validation_log': ['Compliance standard missing']}

graph = StateGraph(ActuatorState)
graph.add_node('validate_torque', validate_torque)
graph.add_node('check_compliance', check_compliance)
graph.set_entry_point('validate_torque')
graph.add_edge('validate_torque', 'check_compliance')
graph.add_edge('check_compliance', END)
graph = graph.compile()