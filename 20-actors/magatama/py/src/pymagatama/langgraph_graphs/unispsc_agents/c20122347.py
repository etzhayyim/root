from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph import StateGraph, END

class ActuatorState(TypedDict):
    spec_id: str
    torque_requirements: float
    precision_level: float
    status: str
    validation_log: List[str]

def validate_torque(state: ActuatorState) -> ActuatorState:
    if state['torque_requirements'] > 0:
        state['validation_log'].append('Torque validated')
    return state

def validate_precision(state: ActuatorState) -> ActuatorState:
    if state['precision_level'] < 0.01:
        state['validation_log'].append('Precision validated')
    state['status'] = 'COMPLETED'
    return state

graph = StateGraph(ActuatorState)
graph.add_node('torque_check', validate_torque)
graph.add_node('precision_check', validate_precision)
graph.set_entry_point('torque_check')
graph.add_edge('torque_check', 'precision_check')
graph.add_edge('precision_check', END)

graph = graph.compile()