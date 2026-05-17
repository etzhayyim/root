from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ActuatorState(TypedDict):
    spec_data: dict
    validation_log: List[str]
    is_compliant: bool

def validate_actuator(state: ActuatorState) -> ActuatorState:
    spec = state['spec_data']
    logs = []
    compliant = True
    if spec.get('torque_nm', 0) <= 0:
        logs.append('Invalid Torque')
        compliant = False
    return {'validation_log': logs, 'is_compliant': compliant}

def process_actuator(state: ActuatorState) -> ActuatorState:
    if state['is_compliant']:
        state['validation_log'].append('Ready for procurement integration')
    return state

graph = StateGraph(ActuatorState)
graph.add_node('validator', validate_actuator)
graph.add_node('processor', process_actuator)
graph.set_entry_point('validator')
graph.add_edge('validator', 'processor')
graph.add_edge('processor', END)
graph = graph.compile()