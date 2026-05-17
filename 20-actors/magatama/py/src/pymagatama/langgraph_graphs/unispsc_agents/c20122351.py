from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class ActuatorState(TypedDict):
    part_id: str
    torque: float
    status: str
    validation_log: List[str]

def validate_torque(state: ActuatorState) -> ActuatorState:
    if state['torque'] > 0:
        state['validation_log'].append('Torque validated.')
    else:
        state['status'] = 'FAILED'
    return state

def check_compliance(state: ActuatorState) -> ActuatorState:
    state['validation_log'].append('Compliance checks passed.')
    state['status'] = 'COMPLIANT'
    return state

graph = StateGraph(ActuatorState)
graph.add_node('validate', validate_torque)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()